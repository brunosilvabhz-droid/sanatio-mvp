from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.antimicrobial_audit import AntimicrobialAudit, AntimicrobialAuditAction


PROTECTED_STATUSES = {"JUSTIFICADO", "INTERVENCAO_SUGERIDA", "RESOLVIDO"}


def _active(row: dict) -> bool:
    return str(row.get("sn_ativo", "")).upper() == "S"


def _priority(days_in_use: int) -> str:
    if days_in_use >= 14:
        return "ALTA"
    if days_in_use >= 7:
        return "MEDIA"
    return "BAIXA"


def _initial_status(active: bool, days_in_use: int) -> str:
    if not active:
        return "ENCERRADO"
    if days_in_use >= 7:
        return "PENDENTE"
    return "MONITORADO"


def sync_for_patient(db: Session, patient: dict, antimicrobials: list[dict], monitoring_run_id: int | None = None) -> int:
    synced = 0
    for item in antimicrobials:
        cd_prescricao = str(item.get("cd_prescricao") or "")
        cd_item_prescricao = str(item.get("cd_item_prescricao") or "")
        if not cd_prescricao or not cd_item_prescricao:
            continue

        active = _active(item)
        days_in_use = int(item.get("dias_uso") or 0)
        audit = db.scalar(
            select(AntimicrobialAudit).where(
                AntimicrobialAudit.cd_prescricao == cd_prescricao,
                AntimicrobialAudit.cd_item_prescricao == cd_item_prescricao,
            )
        )
        if not audit:
            audit = AntimicrobialAudit(
                cd_prescricao=cd_prescricao,
                cd_item_prescricao=cd_item_prescricao,
                status=_initial_status(active, days_in_use),
            )
            db.add(audit)
            synced += 1
        elif audit.status == "MONITORADO" and active and days_in_use >= 7:
            audit.status = "PENDENTE"

        audit.monitoring_run_id = monitoring_run_id
        audit.cd_atendimento = str(patient["cd_atendimento"])
        audit.cd_paciente = str(patient["cd_paciente"])
        audit.unit = patient.get("ds_unidade")
        audit.cd_produto = str(item.get("cd_produto") or "") or None
        audit.antimicrobial_name = str(item.get("ds_antimicrobiano") or "Antimicrobiano nao identificado")
        audit.started_at = item["dt_inicio"]
        audit.ended_at = item.get("dt_fim")
        audit.days_in_use = days_in_use
        audit.active = active
        audit.dose = item.get("ds_dose")
        audit.route = item.get("ds_via")
        audit.frequency = item.get("ds_frequencia")
        audit.priority = _priority(days_in_use)

        if not active and audit.status not in PROTECTED_STATUSES:
            audit.status = "ENCERRADO"

    return synced


def update_audit(
    db: Session,
    audit: AntimicrobialAudit,
    user_id: int,
    status: str,
    decision: str | None,
    comment: str,
) -> AntimicrobialAudit:
    audit.status = status
    audit.decision = decision
    audit.justification = comment
    audit.reviewed_by_user_id = user_id
    audit.reviewed_at = datetime.now(timezone.utc)
    db.add(
        AntimicrobialAuditAction(
            audit_id=audit.id,
            user_id=user_id,
            action="AUDIT_UPDATE",
            status=status,
            decision=decision,
            comment=comment,
        )
    )
    db.commit()
    db.refresh(audit)
    return audit
