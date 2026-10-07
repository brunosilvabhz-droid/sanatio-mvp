from __future__ import annotations

import os
from contextlib import closing
from urllib import error, request

import oracledb
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


SANATIO_API_URL = os.environ.get("SANATIO_API_URL", "https://sanatio.impactocg.com/api").rstrip("/")
SOULMV_DSN = os.environ.get("SOULMV_DSN", "")
RESOLVER_VIEW = os.environ.get("PATIENT_RESOLVER_VIEW", "SANATIO.VW_RESOLVE_PACIENTE")
ALLOWED_ORIGINS = [
    value.strip()
    for value in os.environ.get("PATIENT_RESOLVER_ALLOWED_ORIGINS", "https://sanatio.impactocg.com").split(",")
    if value.strip()
]


class PatientName(BaseModel):
    cd_paciente: str
    nm_paciente: str
    dt_nascimento: str | None = None


def quote_view(value: str) -> str:
    if not value.replace("_", "").replace(".", "").isalnum():
        raise RuntimeError("PATIENT_RESOLVER_VIEW possui nome invalido")
    return value


def initialize_oracle() -> None:
    if os.getenv("SOULMV_ORACLE_THICK", "false").strip().lower() in {"1", "true", "yes", "sim"}:
        oracledb.init_oracle_client()


def authorized_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Autenticacao obrigatoria")
    verification = request.Request(
        f"{SANATIO_API_URL}/auth/me",
        headers={"Authorization": authorization, "Accept": "application/json"},
    )
    try:
        with request.urlopen(verification, timeout=5) as response:
            import json

            user = json.load(response)
    except (error.HTTPError, error.URLError, TimeoutError):
        raise HTTPException(status_code=401, detail="Sessao invalida") from None
    if not user.get("active") or not user.get("can_view_patient_name"):
        raise HTTPException(status_code=403, detail="Usuario sem permissao para visualizar nomes")
    return user


app = FastAPI(title="SANATIO - Resolvedor local de pacientes", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def allow_private_network_access(http_request: Request, call_next):
    response = await call_next(http_request)
    if http_request.headers.get("access-control-request-private-network") == "true":
        response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


@app.on_event("startup")
def startup() -> None:
    if not SOULMV_DSN:
        raise RuntimeError("SOULMV_DSN obrigatoria")
    quote_view(RESOLVER_VIEW)
    initialize_oracle()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/patients/{cd_paciente}", response_model=PatientName)
def resolve_patient(
    cd_paciente: str,
    cd_atendimento: str | None = Query(default=None),
    _: dict = Depends(authorized_user),
) -> PatientName:
    del cd_atendimento  # Mantido no contrato para compatibilidade com o frontend.
    sql = f"""
        SELECT cd_paciente, nm_paciente, dt_nascimento
        FROM {quote_view(RESOLVER_VIEW)}
        WHERE cd_paciente = :cd_paciente
        FETCH FIRST 1 ROW ONLY
    """
    with closing(oracledb.connect(SOULMV_DSN)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(sql, {"cd_paciente": cd_paciente})
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Paciente nao encontrado")
    return PatientName(
        cd_paciente=str(row[0]),
        nm_paciente=str(row[1]),
        dt_nascimento=row[2].isoformat() if row[2] else None,
    )
