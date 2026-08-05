from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any
from urllib import error, request


LOG = logging.getLogger("sanatio_soulmv_integrator")


DEFAULT_CONFIG = "config.hml.json"


@dataclass(frozen=True)
class QuerySpec:
    key: str
    required_columns: tuple[str, ...]
    sql: str


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key).lower(): value for key, value in row.items()}


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().upper() in {"S", "Y", "YES", "TRUE", "1", "ATIVO"}


def iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day).isoformat()
    return str(value)


def safe_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def days_between(start: Any, end: Any | None = None) -> int:
    if not start:
        return 0
    if isinstance(start, datetime):
        start_date = start.date()
    elif isinstance(start, date):
        start_date = start
    else:
        try:
            start_date = datetime.fromisoformat(str(start)).date()
        except ValueError:
            return 0

    if end:
        if isinstance(end, datetime):
            end_date = end.date()
        elif isinstance(end, date):
            end_date = end
        else:
            try:
                end_date = datetime.fromisoformat(str(end)).date()
            except ValueError:
                end_date = datetime.now().date()
    else:
        end_date = datetime.now().date()
    return max((end_date - start_date).days, 0)


def load_config(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as file:
        config = json.load(file)

    config["database"]["engine"] = os.getenv("SOULMV_DB_ENGINE", config["database"].get("engine", "oracle")).lower()
    config["database"]["dsn"] = os.getenv("SOULMV_DSN", config["database"].get("dsn", ""))
    config["sanatio"]["ingest_url"] = os.getenv("SANATIO_INGEST_URL", config["sanatio"].get("ingest_url", ""))
    config["sanatio"]["token"] = os.getenv("SANATIO_TOKEN", config["sanatio"].get("token", ""))
    return config


def quote_view(view_name: str) -> str:
    if not view_name.replace("_", "").replace(".", "").isalnum():
        raise ValueError(f"Nome de view invalido: {view_name}")
    return view_name


def query_specs(views: dict[str, str]) -> list[QuerySpec]:
    patients = quote_view(views["patients"])
    bed_movements = quote_view(views["bed_movements"])
    antimicrobials = quote_view(views["antimicrobials"])
    cultures = quote_view(views["cultures"])
    invasive = quote_view(views["invasive_procedures"])
    isolations = quote_view(views["isolations"])

    return [
        QuerySpec(
            key="patients",
            required_columns=("cd_atendimento", "cd_paciente", "dt_atendimento", "dt_alta", "ds_unidade", "ds_leito"),
            sql=f"""
                SELECT
                    cd_atendimento,
                    cd_paciente,
                    dt_atendimento,
                    dt_alta,
                    ds_unidade,
                    ds_leito
                FROM {patients}
            """,
        ),
        QuerySpec(
            key="bed_movements",
            required_columns=("cd_atendimento", "cd_paciente", "dt_movimentacao"),
            sql=f"""
                SELECT
                    cd_atendimento,
                    cd_paciente,
                    dt_movimentacao,
                    ds_unidade_origem,
                    ds_leito_origem,
                    ds_unidade_destino,
                    ds_leito_destino
                FROM {bed_movements}
            """,
        ),
        QuerySpec(
            key="antimicrobials",
            required_columns=(
                "cd_atendimento",
                "cd_paciente",
                "cd_prescricao",
                "cd_item_prescricao",
                "ds_antimicrobiano",
                "ds_principio_ativo",
                "dt_inicio",
                "dt_aplicacao",
            ),
            sql=f"""
                SELECT *
                FROM {antimicrobials}
            """,
        ),
        QuerySpec(
            key="cultures",
            required_columns=("cd_atendimento", "cd_paciente", "cd_pedido", "cd_exame", "ds_exame", "dt_coleta"),
            sql=f"""
                SELECT
                    cd_atendimento,
                    cd_paciente,
                    cd_pedido,
                    cd_exame,
                    ds_exame,
                    dt_coleta,
                    dt_resultado,
                    ds_material,
                    ds_resultado,
                    ds_microorganismo,
                    sn_positivo
                FROM {cultures}
            """,
        ),
        QuerySpec(
            key="invasive_procedures",
            required_columns=("cd_atendimento", "cd_paciente", "cd_procedimento", "ds_procedimento", "dt_inicio"),
            sql=f"""
                SELECT
                    cd_atendimento,
                    cd_paciente,
                    cd_procedimento,
                    ds_procedimento,
                    dt_inicio,
                    dt_fim,
                    sn_ativo,
                    ds_local_instalacao
                FROM {invasive}
            """,
        ),
        QuerySpec(
            key="isolations",
            required_columns=("cd_atendimento", "cd_paciente", "cd_isolamento", "ds_isolamento", "dt_inicio"),
            sql=f"""
                SELECT
                    cd_atendimento,
                    cd_paciente,
                    cd_isolamento,
                    ds_isolamento,
                    dt_inicio,
                    dt_fim,
                    sn_ativo
                FROM {isolations}
            """,
        ),
    ]


def connect(engine: str, dsn: str):
    if engine == "postgres":
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(dsn, row_factory=dict_row)
    if engine == "oracle":
        import oracledb

        return oracledb.connect(dsn)
    raise ValueError("database.engine deve ser 'oracle' ou 'postgres'")


def fetch_rows(conn, engine: str, spec: QuerySpec) -> list[dict[str, Any]]:
    LOG.info("Lendo %s", spec.key)
    if engine == "postgres":
        rows = conn.execute(spec.sql).fetchall()
        normalized = [normalize_row(dict(row)) for row in rows]
    else:
        cursor = conn.cursor()
        cursor.execute(spec.sql)
        columns = [column[0].lower() for column in cursor.description]
        normalized = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()

    for column in spec.required_columns:
        if normalized and column not in normalized[0]:
            raise RuntimeError(f"View de {spec.key} nao retornou o alias obrigatorio '{column}'")
    LOG.info("%s: %s linhas", spec.key, len(normalized))
    return normalized


def calculate_risk(patient: dict[str, Any], rows: dict[str, list[dict[str, Any]]], thresholds: dict[str, int]) -> dict[str, Any]:
    cd_atendimento = str(patient["cd_atendimento"])
    cultures = [row for row in rows["cultures"] if str(row["cd_atendimento"]) == cd_atendimento]
    antimicrobials = [row for row in rows["antimicrobials"] if str(row["cd_atendimento"]) == cd_atendimento]
    invasive = [row for row in rows["invasive_procedures"] if str(row["cd_atendimento"]) == cd_atendimento]
    isolations = [row for row in rows["isolations"] if str(row["cd_atendimento"]) == cd_atendimento]

    active_antimicrobials = [row for row in antimicrobials if parse_bool(row.get("sn_ativo")) and not row.get("dt_fim")]
    active_invasive = [row for row in invasive if parse_bool(row.get("sn_ativo")) and not row.get("dt_fim")]
    active_isolations = [row for row in isolations if parse_bool(row.get("sn_ativo")) and not row.get("dt_fim")]

    max_antimicrobial_days = max([safe_int(row.get("dias_uso"), days_between(row.get("dt_inicio"), row.get("dt_fim"))) for row in active_antimicrobials] or [0])
    max_invasive_device_days = max([safe_int(row.get("dias_permanencia"), days_between(row.get("dt_inicio"), row.get("dt_fim"))) for row in active_invasive] or [0])
    days_in_hospital = days_between(patient.get("dt_atendimento"), patient.get("dt_alta"))
    has_positive_culture = any(parse_bool(row.get("sn_positivo")) for row in cultures)
    has_active_isolation = bool(active_isolations)

    high = (
        has_positive_culture
        or max_antimicrobial_days >= thresholds["antimicrobial_days_high"]
        or max_invasive_device_days >= thresholds["invasive_device_days_high"]
        or days_in_hospital >= thresholds["hospital_stay_days_high"]
        or has_active_isolation
    )
    medium = max_antimicrobial_days >= thresholds["antimicrobial_days_medium"] or days_in_hospital >= thresholds["hospital_stay_days_medium"]
    risk_status = "alto" if high else "medio" if medium else "baixo"

    return {
        "risk_status": risk_status,
        "days_in_hospital": days_in_hospital,
        "has_positive_culture": has_positive_culture,
        "max_antimicrobial_days": max_antimicrobial_days,
        "max_invasive_device_days": max_invasive_device_days,
        "has_active_isolation": has_active_isolation,
    }


def build_payload(rows: dict[str, list[dict[str, Any]]], thresholds: dict[str, int]) -> dict[str, Any]:
    patients = []
    for row in rows["patients"]:
        patients.append(
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "unit": row.get("ds_unidade"),
                "bed": row.get("ds_leito"),
                "active": row.get("dt_alta") is None,
                "admitted_at": iso(row.get("dt_atendimento")),
                "discharged_at": iso(row.get("dt_alta")),
            }
        )

    return {
        "patients": patients,
        "bed_movements": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "moved_at": iso(row["dt_movimentacao"]),
                "from_unit": row.get("ds_unidade_origem"),
                "from_bed": row.get("ds_leito_origem"),
                "to_unit": row.get("ds_unidade_destino"),
                "to_bed": row.get("ds_leito_destino"),
            }
            for row in rows["bed_movements"]
        ],
        "antimicrobials": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "cd_prescricao": str(row["cd_prescricao"]),
                "cd_item_prescricao": str(row["cd_item_prescricao"]),
                "cd_produto": str(row["cd_produto"]) if row.get("cd_produto") is not None else None,
                "ds_antimicrobiano": row["ds_antimicrobiano"],
                "ds_principio_ativo": row.get("ds_principio_ativo"),
                "dt_inicio": iso(row["dt_inicio"]),
                "dt_aplicacao": iso(row["dt_aplicacao"]),
                "dt_fim": iso(row.get("dt_fim")),
                "sn_ativo": "S" if parse_bool(row.get("sn_ativo", "S")) else "N",
                "ds_frequencia": row.get("ds_frequencia"),
                "ds_via": row.get("ds_via"),
                "ds_dose": row.get("ds_dose"),
                "dias_uso": safe_int(row.get("dias_uso"), days_between(row.get("dt_inicio"), row.get("dt_fim"))),
            }
            for row in rows["antimicrobials"]
        ],
        "cultures": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "cd_pedido": str(row["cd_pedido"]),
                "cd_exame": str(row["cd_exame"]),
                "ds_exame": row["ds_exame"],
                "dt_coleta": iso(row["dt_coleta"]),
                "dt_resultado": iso(row.get("dt_resultado")),
                "ds_material": row.get("ds_material"),
                "ds_microorganismo": row.get("ds_microorganismo"),
                "ds_resultado": row.get("ds_resultado"),
                "sn_positivo": "S" if parse_bool(row.get("sn_positivo")) else "N",
            }
            for row in rows["cultures"]
        ],
        "invasive_procedures": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "cd_procedimento": str(row["cd_procedimento"]),
                "ds_procedimento": row["ds_procedimento"],
                "dt_inicio": iso(row["dt_inicio"]),
                "dt_fim": iso(row.get("dt_fim")),
                "sn_ativo": "S" if parse_bool(row.get("sn_ativo", "S")) else "N",
                "ds_local_instalacao": row.get("ds_local_instalacao"),
                "dias_permanencia": safe_int(row.get("dias_permanencia"), days_between(row.get("dt_inicio"), row.get("dt_fim"))),
            }
            for row in rows["invasive_procedures"]
        ],
        "isolations": [
            {
                "cd_atendimento": str(row["cd_atendimento"]),
                "cd_paciente": str(row["cd_paciente"]),
                "cd_isolamento": str(row["cd_isolamento"]),
                "ds_isolamento": row["ds_isolamento"],
                "dt_inicio": iso(row["dt_inicio"]),
                "dt_fim": iso(row.get("dt_fim")),
                "sn_ativo": "S" if parse_bool(row.get("sn_ativo", "S")) else "N",
            }
            for row in rows["isolations"]
        ],
    }


def post_payload(ingest_url: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        ingest_url,
        data=body,
        headers={"Content-Type": "application/json", "X-Sanatio-Token": token},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"SANATIO retornou HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Nao foi possivel conectar ao SANATIO: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Integrador MV SOUL -> SANATIO.")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Arquivo JSON de configuracao.")
    parser.add_argument("--dry-run", action="store_true", help="Monta o payload e imprime no console sem enviar.")
    parser.add_argument("--output", help="Arquivo para salvar o payload JSON montado.")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"), help="Nivel de log.")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s")
    config = load_config(args.config)
    engine = config["database"]["engine"]
    dsn = config["database"]["dsn"]
    specs = query_specs(config["views"])

    if not dsn:
        LOG.error("DSN do banco nao informado.")
        return 2
    if not config["sanatio"]["token"]:
        LOG.error("Token SANATIO nao informado.")
        return 2

    try:
        with connect(engine, dsn) as conn:
            rows = {spec.key: fetch_rows(conn, engine, spec) for spec in specs}
    except Exception:
        LOG.exception("Falha ao ler views do MV SOUL.")
        return 1

    payload = build_payload(rows, config["risk_thresholds"])
    counts = {key: len(value) for key, value in payload.items()}
    LOG.info("Payload montado: %s", counts)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        LOG.info("Payload salvo em %s", args.output)

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    try:
        result = post_payload(config["sanatio"]["ingest_url"], config["sanatio"]["token"], payload)
    except Exception:
        LOG.exception("Falha ao enviar dados ao SANATIO.")
        return 1

    LOG.info("Resposta SANATIO: %s", json.dumps(result, ensure_ascii=False))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
