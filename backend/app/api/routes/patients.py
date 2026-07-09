from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertRead
from app.schemas.patient import Antimicrobial, Culture, InvasiveProcedure, Isolation, Patient, PatientDetail
from app.services import monitoring_service, soulmv_adapter

router = APIRouter(prefix="/patients", tags=["Pacientes"], dependencies=[Depends(get_current_user)])


def _contains(value: str, needle: str | None) -> bool:
    return not needle or needle.lower() in str(value).lower()


@router.get("", response_model=list[Patient])
def list_patients(
    nome: str | None = None,
    atendimento: str | None = None,
    unidade: str | None = None,
    leito: str | None = None,
    medico: str | None = None,
    convenio: str | None = None,
    status_risco: str | None = Query(default=None),
) -> list[dict]:
    patients = [monitoring_service.patient_with_risk(p) for p in soulmv_adapter.get_patients()]
    return [
        p
        for p in patients
        if _contains(p["nm_paciente"], nome)
        and _contains(p["cd_atendimento"], atendimento)
        and _contains(p["ds_unidade"], unidade)
        and _contains(p["ds_leito"], leito)
        and _contains(p["nm_prestador"], medico)
        and _contains(p["nm_convenio"], convenio)
        and _contains(p["status_risco"], status_risco)
    ]


@router.get("/{cd_atendimento}", response_model=PatientDetail)
def get_patient(cd_atendimento: str) -> dict:
    patient = soulmv_adapter.get_patient(cd_atendimento)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    enriched = monitoring_service.patient_with_risk(patient)
    return {
        "patient": enriched,
        "antimicrobials": soulmv_adapter.get_antimicrobials(cd_atendimento),
        "cultures": soulmv_adapter.get_cultures(cd_atendimento),
        "invasive_procedures": soulmv_adapter.get_invasive_procedures(cd_atendimento),
        "isolations": soulmv_adapter.get_isolations(cd_atendimento),
    }


@router.get("/{cd_atendimento}/antimicrobials", response_model=list[Antimicrobial])
def antimicrobials(cd_atendimento: str) -> list[dict]:
    return soulmv_adapter.get_antimicrobials(cd_atendimento)


@router.get("/{cd_atendimento}/cultures", response_model=list[Culture])
def cultures(cd_atendimento: str) -> list[dict]:
    return soulmv_adapter.get_cultures(cd_atendimento)


@router.get("/{cd_atendimento}/invasive-procedures", response_model=list[InvasiveProcedure])
def invasive_procedures(cd_atendimento: str) -> list[dict]:
    return soulmv_adapter.get_invasive_procedures(cd_atendimento)


@router.get("/{cd_atendimento}/isolations", response_model=list[Isolation])
def isolations(cd_atendimento: str) -> list[dict]:
    return soulmv_adapter.get_isolations(cd_atendimento)


@router.get("/{cd_atendimento}/alerts", response_model=list[AlertRead])
def patient_alerts(cd_atendimento: str, db: Session = Depends(get_db)) -> list[Alert]:
    return list(db.scalars(select(Alert).where(Alert.cd_atendimento == cd_atendimento).order_by(Alert.created_at.desc())))
