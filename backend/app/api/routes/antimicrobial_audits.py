from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.antimicrobial_audit import AntimicrobialAudit, AntimicrobialAuditAction
from app.models.user import User
from app.schemas.antimicrobial_audit import AntimicrobialAuditRead, AntimicrobialAuditUpdate
from app.services import antimicrobial_audit_service

router = APIRouter(prefix="/antimicrobial-audits", tags=["Auditoria de antimicrobianos"])

VALID_STATUSES = {"MONITORADO", "PENDENTE", "EM_ANALISE", "JUSTIFICADO", "INTERVENCAO_SUGERIDA", "RESOLVIDO", "ENCERRADO"}
VALID_DECISIONS = {"MANTER", "DESCALONAR", "SUSPENDER", "TROCAR", "AJUSTAR_DOSE", "COLETAR_CULTURA", "COMUNICAR_MEDICO"}


def _action_to_read(action: AntimicrobialAuditAction) -> dict:
    return {
        "id": action.id,
        "audit_id": action.audit_id,
        "user_id": action.user_id,
        "user_name": action.user.full_name if action.user else None,
        "action": action.action,
        "status": action.status,
        "decision": action.decision,
        "comment": action.comment,
        "created_at": action.created_at,
    }


def _audit_to_read(audit: AntimicrobialAudit) -> AntimicrobialAuditRead:
    return AntimicrobialAuditRead(
        id=audit.id,
        cd_atendimento=audit.cd_atendimento,
        cd_paciente=audit.cd_paciente,
        unit=audit.unit,
        cd_prescricao=audit.cd_prescricao,
        cd_item_prescricao=audit.cd_item_prescricao,
        cd_produto=audit.cd_produto,
        antimicrobial_name=audit.antimicrobial_name,
        started_at=audit.started_at,
        ended_at=audit.ended_at,
        days_in_use=audit.days_in_use,
        active=audit.active,
        dose=audit.dose,
        route=audit.route,
        frequency=audit.frequency,
        status=audit.status,
        priority=audit.priority,
        decision=audit.decision,
        justification=audit.justification,
        reviewed_by_user_id=audit.reviewed_by_user_id,
        reviewed_by_name=audit.reviewed_by.full_name if audit.reviewed_by else None,
        reviewed_at=audit.reviewed_at,
        created_at=audit.created_at,
        updated_at=audit.updated_at,
        actions=[_action_to_read(action) for action in audit.actions],
    )


@router.get("", response_model=list[AntimicrobialAuditRead])
def list_audits(
    status: str | None = None,
    priority: str | None = None,
    unidade: str | None = None,
    atendimento: str | None = None,
    paciente: str | None = None,
    antimicrobial: str | None = None,
    min_days: int | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AntimicrobialAuditRead]:
    stmt = (
        select(AntimicrobialAudit)
        .options(
            selectinload(AntimicrobialAudit.actions).selectinload(AntimicrobialAuditAction.user),
            selectinload(AntimicrobialAudit.reviewed_by),
        )
        .order_by(AntimicrobialAudit.priority.desc(), AntimicrobialAudit.days_in_use.desc(), AntimicrobialAudit.updated_at.desc())
    )
    if status:
        stmt = stmt.where(AntimicrobialAudit.status == status)
    if priority:
        stmt = stmt.where(AntimicrobialAudit.priority == priority)
    if unidade:
        stmt = stmt.where(AntimicrobialAudit.unit.ilike(f"%{unidade}%"))
    if atendimento:
        stmt = stmt.where(AntimicrobialAudit.cd_atendimento.ilike(f"%{atendimento}%"))
    if paciente:
        stmt = stmt.where(AntimicrobialAudit.cd_paciente.ilike(f"%{paciente}%"))
    if antimicrobial:
        stmt = stmt.where(AntimicrobialAudit.antimicrobial_name.ilike(f"%{antimicrobial}%"))
    if min_days is not None:
        stmt = stmt.where(AntimicrobialAudit.days_in_use >= min_days)
    if active_only:
        stmt = stmt.where(AntimicrobialAudit.active.is_(True))
    return [_audit_to_read(audit) for audit in db.scalars(stmt).all()]


@router.patch("/{audit_id}", response_model=AntimicrobialAuditRead)
def update_audit(
    audit_id: int,
    payload: AntimicrobialAuditUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AntimicrobialAuditRead:
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail="Status invalido")
    if payload.decision and payload.decision not in VALID_DECISIONS:
        raise HTTPException(status_code=422, detail="Decisao invalida")
    if not payload.comment.strip():
        raise HTTPException(status_code=422, detail="Justificativa obrigatoria")

    audit = db.scalar(
        select(AntimicrobialAudit)
        .options(
            selectinload(AntimicrobialAudit.actions).selectinload(AntimicrobialAuditAction.user),
            selectinload(AntimicrobialAudit.reviewed_by),
        )
        .where(AntimicrobialAudit.id == audit_id)
    )
    if not audit:
        raise HTTPException(status_code=404, detail="Auditoria nao encontrada")

    antimicrobial_audit_service.update_audit(db, audit, current_user.id, payload.status, payload.decision, payload.comment)
    audit = db.scalar(
        select(AntimicrobialAudit)
        .options(
            selectinload(AntimicrobialAudit.actions).selectinload(AntimicrobialAuditAction.user),
            selectinload(AntimicrobialAudit.reviewed_by),
        )
        .where(AntimicrobialAudit.id == audit_id)
    )
    return _audit_to_read(audit)
