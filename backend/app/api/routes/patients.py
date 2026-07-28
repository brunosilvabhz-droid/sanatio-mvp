from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.alert import Alert, AlertAction
from app.models.antimicrobial_audit import AntimicrobialAudit, AntimicrobialAuditAction
from app.models.intervention import InterventionRecipient, InterventionRequest
from app.models.patient_bed_movement import PatientBedMovement
from app.models.patient_monitoring_snapshot import PatientMonitoringSnapshot
from app.models.patient_timeline_note import PatientTimelineNote
from app.models.user import User
from app.schemas.alert import AlertRead
from app.schemas.intervention import PatientTimelineNoteCreate, TimelineEventRead
from app.schemas.patient import Antimicrobial, Culture, InvasiveProcedure, Isolation, Patient, PatientDetail
from app.services import monitoring_service, soulmv_adapter

router = APIRouter(prefix="/patients", tags=["Pacientes"])


def _contains(value: str, needle: str | None) -> bool:
    return not needle or needle.lower() in str(value).lower()


def _can_return_patient_name(user: User) -> bool:
    return settings.expose_patient_names_in_api and user.can_view_patient_name


def _patients_for_user(user: User) -> list[dict]:
    patients = soulmv_adapter.get_patients_internal()
    if _can_return_patient_name(user):
        return patients
    return [{**patient, "nm_paciente": None} for patient in patients]


def _latest_snapshots(db: Session) -> list[PatientMonitoringSnapshot]:
    snapshots = db.scalars(select(PatientMonitoringSnapshot).order_by(PatientMonitoringSnapshot.collected_at.desc())).all()
    latest: dict[str, PatientMonitoringSnapshot] = {}
    for snapshot in snapshots:
        latest.setdefault(snapshot.cd_atendimento, snapshot)
    return list(latest.values())


def _snapshot_to_patient(snapshot: PatientMonitoringSnapshot) -> dict:
    today = date.today()
    admitted_at = snapshot.admitted_at or datetime.now(timezone.utc)
    return {
        "cd_atendimento": snapshot.cd_atendimento,
        "cd_paciente": snapshot.cd_paciente,
        "nm_paciente": None,
        "dt_nascimento": today,
        "tp_sexo": "-",
        "dt_atendimento": admitted_at,
        "cd_unidade": snapshot.unit or "-",
        "ds_unidade": snapshot.unit or "-",
        "cd_leito": snapshot.bed or "-",
        "ds_leito": snapshot.bed or "-",
        "active": snapshot.active,
        "discharged_at": snapshot.discharged_at,
        "cd_prestador": "-",
        "nm_prestador": "-",
        "cd_convenio": "-",
        "nm_convenio": "-",
        "idade": 0,
        "dias_internacao": snapshot.days_in_hospital,
        "status_risco": snapshot.risk_status,
        "risk_reasons": _snapshot_reasons(snapshot),
    }


def _snapshot_reasons(snapshot: PatientMonitoringSnapshot) -> list[str]:
    reasons = []
    if snapshot.risk_status == "alto":
        reasons.append("Risco alto recebido do hospital")
    if snapshot.has_positive_culture:
        reasons.append("Cultura positiva")
    if snapshot.max_antimicrobial_days:
        reasons.append(f"Antimicrobiano por {snapshot.max_antimicrobial_days} dias")
    if snapshot.max_invasive_device_days:
        reasons.append(f"Procedimento invasivo por {snapshot.max_invasive_device_days} dias")
    if snapshot.has_active_isolation:
        reasons.append("Isolamento ativo")
    if snapshot.days_in_hospital:
        reasons.append(f"{snapshot.days_in_hospital} dias de internacao")
    return reasons


@router.get("", response_model=list[Patient])
def list_patients(
    nome: str | None = None,
    atendimento: str | None = None,
    unidade: str | None = None,
    leito: str | None = None,
    medico: str | None = None,
    convenio: str | None = None,
    status_risco: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    snapshots = _latest_snapshots(db)
    patients = [_snapshot_to_patient(snapshot) for snapshot in snapshots] if snapshots else [monitoring_service.patient_with_risk(p) for p in _patients_for_user(current_user)]
    return [
        p
        for p in patients
        if _contains(p["cd_paciente"], nome)
        and _contains(p["cd_atendimento"], atendimento)
        and _contains(p["ds_unidade"], unidade)
        and _contains(p["ds_leito"], leito)
        and _contains(p["nm_prestador"], medico)
        and _contains(p["nm_convenio"], convenio)
        and _contains(p["status_risco"], status_risco)
    ]


@router.get("/{cd_atendimento}", response_model=PatientDetail)
def get_patient(cd_atendimento: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    snapshot = db.scalar(
        select(PatientMonitoringSnapshot)
        .where(PatientMonitoringSnapshot.cd_atendimento == cd_atendimento)
        .order_by(PatientMonitoringSnapshot.collected_at.desc())
    )
    if snapshot:
        return {
            "patient": _snapshot_to_patient(snapshot),
            "antimicrobials": [],
            "cultures": [],
            "invasive_procedures": [],
            "isolations": [],
        }

    patient = next((p for p in _patients_for_user(current_user) if str(p["cd_atendimento"]) == str(cd_atendimento)), None)
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


@router.get("/{cd_paciente}/history")
def patient_history(cd_paciente: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    snapshots = db.scalars(
        select(PatientMonitoringSnapshot)
        .where(PatientMonitoringSnapshot.cd_paciente == cd_paciente)
        .order_by(PatientMonitoringSnapshot.collected_at.desc())
    ).all()
    latest: dict[str, PatientMonitoringSnapshot] = {}
    for snapshot in snapshots:
        latest.setdefault(snapshot.cd_atendimento, snapshot)
    if not latest:
        raise HTTPException(status_code=404, detail="Paciente nao encontrado")

    attendances = []
    for snapshot in sorted(latest.values(), key=lambda item: item.admitted_at or item.collected_at, reverse=True):
        alerts_count = db.scalar(select(func.count(Alert.id)).where(Alert.cd_atendimento == snapshot.cd_atendimento)) or 0
        open_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.cd_atendimento == snapshot.cd_atendimento, Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
        interventions_count = db.scalar(select(func.count(InterventionRequest.id)).where(InterventionRequest.cd_atendimento == snapshot.cd_atendimento)) or 0
        antimicrobial_audits_count = db.scalar(select(func.count(AntimicrobialAudit.id)).where(AntimicrobialAudit.cd_atendimento == snapshot.cd_atendimento)) or 0
        bed_movements_count = db.scalar(select(func.count(PatientBedMovement.id)).where(PatientBedMovement.cd_atendimento == snapshot.cd_atendimento)) or 0
        attendances.append(
            {
                "patient": _snapshot_to_patient(snapshot),
                "summary": {
                    "alerts": alerts_count,
                    "open_alerts": open_alerts,
                    "interventions": interventions_count,
                    "antimicrobial_audits": antimicrobial_audits_count,
                    "invasive_procedures": 1 if snapshot.max_invasive_device_days > 0 else 0,
                    "antimicrobials": 1 if snapshot.max_antimicrobial_days > 0 else 0,
                    "bed_movements": bed_movements_count,
                },
            }
        )

    return {"cd_paciente": cd_paciente, "attendances": attendances}


@router.get("/{cd_atendimento}/antimicrobials", response_model=list[Antimicrobial])
def antimicrobials(cd_atendimento: str, _: User = Depends(get_current_user)) -> list[dict]:
    return soulmv_adapter.get_antimicrobials(cd_atendimento)


@router.get("/{cd_atendimento}/cultures", response_model=list[Culture])
def cultures(cd_atendimento: str, _: User = Depends(get_current_user)) -> list[dict]:
    return soulmv_adapter.get_cultures(cd_atendimento)


@router.get("/{cd_atendimento}/invasive-procedures", response_model=list[InvasiveProcedure])
def invasive_procedures(cd_atendimento: str, _: User = Depends(get_current_user)) -> list[dict]:
    return soulmv_adapter.get_invasive_procedures(cd_atendimento)


@router.get("/{cd_atendimento}/isolations", response_model=list[Isolation])
def isolations(cd_atendimento: str, _: User = Depends(get_current_user)) -> list[dict]:
    return soulmv_adapter.get_isolations(cd_atendimento)


@router.get("/{cd_atendimento}/alerts", response_model=list[AlertRead])
def patient_alerts(cd_atendimento: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[Alert]:
    return list(db.scalars(select(Alert).where(Alert.cd_atendimento == cd_atendimento).order_by(Alert.created_at.desc())))


@router.post("/{cd_atendimento}/timeline-notes", response_model=TimelineEventRead)
def add_timeline_note(
    cd_atendimento: str,
    payload: PatientTimelineNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not payload.note.strip():
        raise HTTPException(status_code=422, detail="Evolucao obrigatoria")
    note = PatientTimelineNote(
        cd_atendimento=cd_atendimento,
        cd_paciente=payload.cd_paciente,
        note_type=payload.note_type,
        note=payload.note,
        user_id=current_user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {
        "id": f"note-{note.id}",
        "type": note.note_type,
        "title": "Evolucao SCIH",
        "description": note.note,
        "status": None,
        "actor": current_user.full_name,
        "created_at": note.created_at,
    }


@router.get("/{cd_atendimento}/timeline", response_model=list[TimelineEventRead])
def patient_timeline(cd_atendimento: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
    events: list[dict] = []
    snapshots = db.scalars(select(PatientMonitoringSnapshot).where(PatientMonitoringSnapshot.cd_atendimento == cd_atendimento).order_by(PatientMonitoringSnapshot.collected_at.desc()).limit(20)).all()
    for snapshot in snapshots:
        events.append(
            {
                "id": f"snapshot-{snapshot.id}",
                "type": "SNAPSHOT",
                "title": f"Snapshot de risco {snapshot.risk_status}",
                "description": (
                    f"{snapshot.days_in_hospital} dias internado; antimicrobiano max. {snapshot.max_antimicrobial_days} dias; "
                    f"procedimento invasivo max. {snapshot.max_invasive_device_days} dias"
                ),
                "status": snapshot.risk_status,
                "actor": "SANATIO",
                "created_at": snapshot.collected_at,
            }
        )

    movements = db.scalars(select(PatientBedMovement).where(PatientBedMovement.cd_atendimento == cd_atendimento)).all()
    for movement in movements:
        events.append(
            {
                "id": f"bed-movement-{movement.id}",
                "type": "MOVIMENTACAO_LEITO",
                "title": "Movimentacao de leito",
                "description": f"{movement.from_unit or '-'} / {movement.from_bed or '-'} -> {movement.to_unit or '-'} / {movement.to_bed or '-'}",
                "status": None,
                "actor": "MV Soul",
                "created_at": movement.moved_at,
            }
        )

    notes = db.scalars(select(PatientTimelineNote).options(selectinload(PatientTimelineNote.user)).where(PatientTimelineNote.cd_atendimento == cd_atendimento)).all()
    for note in notes:
        events.append({"id": f"note-{note.id}", "type": note.note_type, "title": "Evolucao SCIH", "description": note.note, "status": None, "actor": note.user.full_name if note.user else "Sistema", "created_at": note.created_at})

    alerts = db.scalars(select(Alert).options(selectinload(Alert.actions).selectinload(AlertAction.user)).where(Alert.cd_atendimento == cd_atendimento)).all()
    for alert in alerts:
        events.append({"id": f"alert-{alert.id}", "type": "ALERTA", "title": alert.title, "description": alert.description, "status": alert.status, "actor": "SANATIO", "created_at": alert.created_at})
        for action in alert.actions:
            events.append(
                {
                    "id": f"alert-action-{action.id}",
                    "type": "ACAO_ALERTA",
                    "title": action.action,
                    "description": action.comment,
                    "status": alert.status,
                    "actor": action.user.full_name if action.user else "Sistema",
                    "created_at": action.created_at,
                }
            )

    audits = db.scalars(select(AntimicrobialAudit).options(selectinload(AntimicrobialAudit.actions).selectinload(AntimicrobialAuditAction.user)).where(AntimicrobialAudit.cd_atendimento == cd_atendimento)).all()
    for audit in audits:
        events.append(
            {
                "id": f"audit-{audit.id}",
                "type": "ANTIMICROBIANO",
                "title": audit.antimicrobial_name,
                "description": f"{audit.days_in_use} dias de uso; {audit.dose or '-'} | {audit.route or '-'} | {audit.frequency or '-'}",
                "status": audit.status,
                "actor": "SANATIO",
                "created_at": audit.created_at,
            }
        )
        for action in audit.actions:
            events.append({"id": f"audit-action-{action.id}", "type": "ACAO_ANTIMICROBIANO", "title": action.action, "description": action.comment, "status": action.status, "actor": action.user.full_name if action.user else "Sistema", "created_at": action.created_at})

    interventions = db.scalars(
        select(InterventionRequest)
        .options(
            selectinload(InterventionRequest.requested_by),
            selectinload(InterventionRequest.responded_by),
            selectinload(InterventionRequest.recipients).selectinload(InterventionRecipient.user),
        )
        .where(InterventionRequest.cd_atendimento == cd_atendimento)
    ).all()
    for intervention in interventions:
        recipients = ", ".join(recipient.user.full_name for recipient in intervention.recipients if recipient.user)
        events.append(
            {
                "id": f"intervention-{intervention.id}",
                "type": "INTERVENCAO",
                "title": f"Intervencao {intervention.status}",
                "description": f"{intervention.reason}. Destinatarios: {recipients or '-'}",
                "status": intervention.status,
                "actor": intervention.requested_by.full_name if intervention.requested_by else "Sistema",
                "created_at": intervention.created_at,
            }
        )
        if intervention.responded_at:
            events.append(
                {
                    "id": f"intervention-response-{intervention.id}",
                    "type": "RESPOSTA_INTERVENCAO",
                    "title": intervention.response or "Resposta",
                    "description": intervention.response_justification,
                    "status": intervention.status,
                    "actor": intervention.responded_by.full_name if intervention.responded_by else "Destinatario",
                    "created_at": intervention.responded_at,
                }
            )
    return sorted(events, key=lambda item: item["created_at"], reverse=True)
