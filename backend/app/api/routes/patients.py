from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert, AlertAction
from app.models.antimicrobial_audit import AntimicrobialAudit, AntimicrobialAuditAction
from app.models.clinical import (
    AntimicrobianoAtendimento,
    Atendimento,
    CulturaAtendimento,
    IsolamentoAtendimento,
    MovimentacaoLeito,
    ProcedimentoInvasivoAtendimento,
    SnapshotAtendimento,
)
from app.models.intervention import InterventionRecipient, InterventionRequest
from app.models.patient_bed_movement import PatientBedMovement
from app.models.patient_monitoring_snapshot import PatientMonitoringSnapshot
from app.models.patient_timeline_note import PatientTimelineNote
from app.models.user import User
from app.schemas.alert import AlertRead
from app.schemas.intervention import PatientTimelineNoteCreate, TimelineEventRead
from app.schemas.patient import Antimicrobial, Culture, InvasiveProcedure, Isolation, Patient, PatientDetail

router = APIRouter(prefix="/patients", tags=["Pacientes"])


def _contains(value: str, needle: str | None) -> bool:
    return not needle or needle.lower() in str(value).lower()


def _latest_snapshots(db: Session) -> list[PatientMonitoringSnapshot]:
    snapshots = db.scalars(select(PatientMonitoringSnapshot).order_by(PatientMonitoringSnapshot.collected_at.desc())).all()
    latest: dict[str, PatientMonitoringSnapshot] = {}
    for snapshot in snapshots:
        latest.setdefault(snapshot.cd_atendimento, snapshot)
    return list(latest.values())


def _latest_clinical_snapshots(db: Session) -> list[SnapshotAtendimento]:
    snapshots = db.scalars(
        select(SnapshotAtendimento)
        .join(SnapshotAtendimento.atendimento)
        .order_by(SnapshotAtendimento.data_hora_coleta.desc())
    ).all()
    latest: dict[str, SnapshotAtendimento] = {}
    for snapshot in snapshots:
        latest.setdefault(snapshot.atendimento.id_origem_atendimento, snapshot)
    return list(latest.values())


def _clinical_snapshot_to_patient(snapshot: SnapshotAtendimento) -> dict:
    attendance = snapshot.atendimento
    today = date.today()
    admitted_at = attendance.data_hora_entrada or datetime.now(timezone.utc)
    return {
        "cd_atendimento": attendance.id_origem_atendimento,
        "cd_paciente": attendance.paciente.id_origem_paciente,
        "nm_paciente": None,
        "dt_nascimento": today,
        "tp_sexo": "-",
        "dt_atendimento": admitted_at,
        "cd_unidade": attendance.unidade_atual or "-",
        "ds_unidade": attendance.unidade_atual or "-",
        "cd_leito": attendance.leito_atual or "-",
        "ds_leito": attendance.leito_atual or "-",
        "active": attendance.ativo,
        "discharged_at": attendance.data_hora_saida,
        "cd_prestador": "-",
        "nm_prestador": "-",
        "cd_convenio": "-",
        "nm_convenio": "-",
        "idade": 0,
        "dias_internacao": snapshot.dias_internacao,
        "status_risco": snapshot.status_risco,
        "risk_reasons": _clinical_snapshot_reasons(snapshot),
    }


def _clinical_snapshot_reasons(snapshot: SnapshotAtendimento) -> list[str]:
    reasons = []
    if snapshot.status_risco == "alto":
        reasons.append("Risco alto recebido do hospital")
    if snapshot.possui_cultura_positiva:
        reasons.append("Cultura positiva")
    if snapshot.maior_dias_antimicrobiano:
        reasons.append(f"Antimicrobiano por {snapshot.maior_dias_antimicrobiano} dias")
    if snapshot.maior_dias_dispositivo_invasivo:
        reasons.append(f"Procedimento invasivo por {snapshot.maior_dias_dispositivo_invasivo} dias")
    if snapshot.possui_isolamento_ativo:
        reasons.append("Isolamento ativo")
    if snapshot.dias_internacao:
        reasons.append(f"{snapshot.dias_internacao} dias de internacao")
    return reasons


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


def _antimicrobial_to_read(item: AntimicrobianoAtendimento, attendance: Atendimento) -> dict:
    return {
        "cd_atendimento": attendance.id_origem_atendimento,
        "cd_paciente": attendance.paciente.id_origem_paciente,
        "cd_prescricao": item.id_origem_prescricao,
        "cd_item_prescricao": item.id_origem_item_prescricao,
        "cd_produto": item.id_origem_produto or "",
        "ds_antimicrobiano": item.nome_antimicrobiano,
        "ds_principio_ativo": item.principio_ativo or item.nome_antimicrobiano,
        "dt_inicio": item.data_hora_inicio,
        "dt_aplicacao": item.data_hora_aplicacao,
        "dt_fim": item.data_hora_fim,
        "sn_ativo": "S" if item.ativo else "N",
        "ds_frequencia": item.frequencia or "",
        "ds_via": item.via or "",
        "ds_dose": item.dose or "",
        "dias_uso": item.dias_uso,
    }


def _culture_to_read(item: CulturaAtendimento, attendance: Atendimento) -> dict:
    return {
        "cd_atendimento": attendance.id_origem_atendimento,
        "cd_paciente": attendance.paciente.id_origem_paciente,
        "cd_pedido": item.id_origem_pedido,
        "cd_exame": item.id_origem_exame,
        "ds_exame": item.exame,
        "dt_coleta": item.data_hora_coleta,
        "dt_resultado": item.data_hora_resultado,
        "ds_material": item.material or "",
        "ds_microorganismo": item.microorganismo,
        "ds_resultado": item.resultado or "",
        "sn_positivo": "S" if item.positivo else "N",
    }


def _procedure_to_read(item: ProcedimentoInvasivoAtendimento, attendance: Atendimento) -> dict:
    return {
        "cd_atendimento": attendance.id_origem_atendimento,
        "cd_paciente": attendance.paciente.id_origem_paciente,
        "cd_procedimento": item.id_origem_procedimento,
        "ds_procedimento": item.procedimento,
        "dt_inicio": item.data_hora_inicio,
        "dt_fim": item.data_hora_fim,
        "sn_ativo": "S" if item.ativo else "N",
        "ds_local_instalacao": item.local_instalacao or "",
        "dias_permanencia": item.dias_permanencia,
    }


def _isolation_to_read(item: IsolamentoAtendimento, attendance: Atendimento) -> dict:
    return {
        "cd_atendimento": attendance.id_origem_atendimento,
        "cd_paciente": attendance.paciente.id_origem_paciente,
        "cd_isolamento": item.id_origem_isolamento,
        "ds_isolamento": item.isolamento,
        "dt_inicio": item.data_hora_inicio,
        "dt_fim": item.data_hora_fim,
        "sn_ativo": "S" if item.ativo else "N",
    }


def _detail_rows(db: Session, attendance: Atendimento) -> dict:
    antimicrobials = db.scalars(select(AntimicrobianoAtendimento).where(AntimicrobianoAtendimento.atendimento_id == attendance.id).order_by(AntimicrobianoAtendimento.ativo.desc(), AntimicrobianoAtendimento.dias_uso.desc())).all()
    cultures = db.scalars(select(CulturaAtendimento).where(CulturaAtendimento.atendimento_id == attendance.id).order_by(CulturaAtendimento.data_hora_coleta.desc())).all()
    procedures = db.scalars(select(ProcedimentoInvasivoAtendimento).where(ProcedimentoInvasivoAtendimento.atendimento_id == attendance.id).order_by(ProcedimentoInvasivoAtendimento.ativo.desc(), ProcedimentoInvasivoAtendimento.dias_permanencia.desc())).all()
    isolations = db.scalars(select(IsolamentoAtendimento).where(IsolamentoAtendimento.atendimento_id == attendance.id).order_by(IsolamentoAtendimento.ativo.desc(), IsolamentoAtendimento.data_hora_inicio.desc())).all()
    return {
        "antimicrobials": [_antimicrobial_to_read(item, attendance) for item in antimicrobials],
        "cultures": [_culture_to_read(item, attendance) for item in cultures],
        "invasive_procedures": [_procedure_to_read(item, attendance) for item in procedures],
        "isolations": [_isolation_to_read(item, attendance) for item in isolations],
    }


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
    _: User = Depends(get_current_user),
) -> list[dict]:
    clinical_snapshots = _latest_clinical_snapshots(db)
    if clinical_snapshots:
        patients = [_clinical_snapshot_to_patient(snapshot) for snapshot in clinical_snapshots]
    else:
        snapshots = _latest_snapshots(db)
        patients = [_snapshot_to_patient(snapshot) for snapshot in snapshots] if snapshots else []
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
def get_patient(cd_atendimento: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    clinical_snapshot = db.scalar(
        select(SnapshotAtendimento)
        .join(SnapshotAtendimento.atendimento)
        .where(Atendimento.id_origem_atendimento == cd_atendimento)
        .order_by(SnapshotAtendimento.data_hora_coleta.desc())
    )
    if clinical_snapshot:
        rows = _detail_rows(db, clinical_snapshot.atendimento)
        return {
            "patient": _clinical_snapshot_to_patient(clinical_snapshot),
            **rows,
        }

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

    raise HTTPException(status_code=404, detail="Paciente nao encontrado")


@router.get("/{identifier}/history")
def patient_history(identifier: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    attendance_by_identifier = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == identifier))
    cd_paciente = attendance_by_identifier.paciente.id_origem_paciente if attendance_by_identifier else identifier

    clinical_snapshots = db.scalars(
        select(SnapshotAtendimento)
        .join(SnapshotAtendimento.atendimento)
        .join(Atendimento.paciente)
        .where(Atendimento.paciente.has(id_origem_paciente=cd_paciente))
        .order_by(SnapshotAtendimento.data_hora_coleta.desc())
    ).all()
    latest_clinical: dict[str, SnapshotAtendimento] = {}
    for snapshot in clinical_snapshots:
        latest_clinical.setdefault(snapshot.atendimento.id_origem_atendimento, snapshot)
    if latest_clinical:
        attendances = []
        for snapshot in sorted(latest_clinical.values(), key=lambda item: item.atendimento.data_hora_entrada or item.data_hora_coleta, reverse=True):
            cd_atendimento = snapshot.atendimento.id_origem_atendimento
            alerts_count = db.scalar(select(func.count(Alert.id)).where(Alert.cd_atendimento == cd_atendimento)) or 0
            open_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.cd_atendimento == cd_atendimento, Alert.status.in_(["ABERTO", "EM_ANALISE"]))) or 0
            interventions_count = db.scalar(select(func.count(InterventionRequest.id)).where(InterventionRequest.cd_atendimento == cd_atendimento)) or 0
            antimicrobial_audits_count = db.scalar(select(func.count(AntimicrobialAudit.id)).where(AntimicrobialAudit.cd_atendimento == cd_atendimento)) or 0
            bed_movements_count = db.scalar(select(func.count(MovimentacaoLeito.id)).where(MovimentacaoLeito.atendimento_id == snapshot.atendimento_id)) or 0
            procedures_count = db.scalar(select(func.count(ProcedimentoInvasivoAtendimento.id)).where(ProcedimentoInvasivoAtendimento.atendimento_id == snapshot.atendimento_id)) or 0
            antimicrobials_count = db.scalar(select(func.count(AntimicrobianoAtendimento.id)).where(AntimicrobianoAtendimento.atendimento_id == snapshot.atendimento_id)) or 0
            attendances.append(
                {
                    "patient": _clinical_snapshot_to_patient(snapshot),
                    "summary": {
                        "alerts": alerts_count,
                        "open_alerts": open_alerts,
                        "interventions": interventions_count,
                        "antimicrobial_audits": antimicrobial_audits_count,
                        "invasive_procedures": procedures_count,
                        "antimicrobials": antimicrobials_count,
                        "bed_movements": bed_movements_count,
                    },
                }
            )
        return {"cd_paciente": cd_paciente, "attendances": attendances}

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
def antimicrobials(cd_atendimento: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
    attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == cd_atendimento))
    if not attendance:
        return []
    return _detail_rows(db, attendance)["antimicrobials"]


@router.get("/{cd_atendimento}/cultures", response_model=list[Culture])
def cultures(cd_atendimento: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
    attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == cd_atendimento))
    if not attendance:
        return []
    return _detail_rows(db, attendance)["cultures"]


@router.get("/{cd_atendimento}/invasive-procedures", response_model=list[InvasiveProcedure])
def invasive_procedures(cd_atendimento: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
    attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == cd_atendimento))
    if not attendance:
        return []
    return _detail_rows(db, attendance)["invasive_procedures"]


@router.get("/{cd_atendimento}/isolations", response_model=list[Isolation])
def isolations(cd_atendimento: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
    attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == cd_atendimento))
    if not attendance:
        return []
    return _detail_rows(db, attendance)["isolations"]


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
    attendance = db.scalar(select(Atendimento).where(Atendimento.id_origem_atendimento == cd_atendimento))
    if attendance:
        clinical_snapshots = db.scalars(select(SnapshotAtendimento).where(SnapshotAtendimento.atendimento_id == attendance.id).order_by(SnapshotAtendimento.data_hora_coleta.desc()).limit(20)).all()
        for snapshot in clinical_snapshots:
            events.append(
                {
                    "id": f"snapshot-atendimento-{snapshot.id}",
                    "type": "SNAPSHOT",
                    "title": f"Snapshot de risco {snapshot.status_risco}",
                    "description": (
                        f"{snapshot.dias_internacao} dias internado; antimicrobiano max. {snapshot.maior_dias_antimicrobiano} dias; "
                        f"procedimento invasivo max. {snapshot.maior_dias_dispositivo_invasivo} dias"
                    ),
                    "status": snapshot.status_risco,
                    "actor": "SANATIO",
                    "created_at": snapshot.data_hora_coleta,
                }
            )

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

    if attendance:
        clinical_movements = db.scalars(select(MovimentacaoLeito).where(MovimentacaoLeito.atendimento_id == attendance.id)).all()
        for movement in clinical_movements:
            events.append(
                {
                    "id": f"movimentacao-leito-{movement.id}",
                    "type": "MOVIMENTACAO_LEITO",
                    "title": "Movimentacao de leito",
                    "description": f"{movement.unidade_origem or '-'} / {movement.leito_origem or '-'} -> {movement.unidade_destino or '-'} / {movement.leito_destino or '-'}",
                    "status": None,
                    "actor": "MV Soul",
                    "created_at": movement.data_hora_movimentacao,
                }
            )

        clinical_rows = _detail_rows(db, attendance)
        for item in clinical_rows["antimicrobials"]:
            events.append(
                {
                    "id": f"antimicrobiano-{item['cd_prescricao']}-{item['cd_item_prescricao']}-{item['dt_aplicacao'] or item['dt_inicio']}",
                    "type": "ANTIMICROBIANO",
                    "title": item["ds_antimicrobiano"],
                    "description": (
                        f"Principio ativo: {item['ds_principio_ativo']}; {item['dias_uso']} dias de uso; "
                        f"{item['ds_dose'] or '-'} | {item['ds_via'] or '-'} | {item['ds_frequencia'] or '-'}"
                    ),
                    "status": "ATIVO" if item["sn_ativo"] == "S" else "ENCERRADO",
                    "actor": "Integracao hospitalar",
                    "created_at": item["dt_aplicacao"] or item["dt_inicio"],
                }
            )
        for item in clinical_rows["cultures"]:
            events.append(
                {
                    "id": f"cultura-{item['cd_pedido']}-{item['cd_exame']}",
                    "type": "CULTURA",
                    "title": item["ds_exame"],
                    "description": f"{item['ds_material']}: {item['ds_resultado'] or '-'} {item['ds_microorganismo'] or ''}".strip(),
                    "status": "POSITIVA" if item["sn_positivo"] == "S" else "NAO_POSITIVA",
                    "actor": "Integracao hospitalar",
                    "created_at": item["dt_resultado"] or item["dt_coleta"],
                }
            )
        for item in clinical_rows["invasive_procedures"]:
            events.append(
                {
                    "id": f"procedimento-{item['cd_procedimento']}-{item['dt_inicio']}",
                    "type": "PROCEDIMENTO_INVASIVO",
                    "title": item["ds_procedimento"],
                    "description": f"{item['dias_permanencia']} dias; local: {item['ds_local_instalacao'] or '-'}",
                    "status": "ATIVO" if item["sn_ativo"] == "S" else "ENCERRADO",
                    "actor": "Integracao hospitalar",
                    "created_at": item["dt_inicio"],
                }
            )
        for item in clinical_rows["isolations"]:
            events.append(
                {
                    "id": f"isolamento-{item['cd_isolamento']}-{item['dt_inicio']}",
                    "type": "ISOLAMENTO",
                    "title": item["ds_isolamento"],
                    "description": "Isolamento ativo" if item["sn_ativo"] == "S" else "Isolamento encerrado",
                    "status": "ATIVO" if item["sn_ativo"] == "S" else "ENCERRADO",
                    "actor": "Integracao hospitalar",
                    "created_at": item["dt_inicio"],
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
