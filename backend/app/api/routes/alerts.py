from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertActionCreate, AlertActionRead, AlertRead, AlertStatusUpdate
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alertas"])


@router.get("", response_model=list[AlertRead])
def list_alerts(
    status: str | None = None,
    severity: str | None = None,
    unidade: str | None = None,
    atendimento: str | None = None,
    paciente: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Alert]:
    stmt = select(Alert).options(selectinload(Alert.actions)).order_by(Alert.created_at.desc())
    if status:
        stmt = stmt.where(Alert.status == status)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if unidade:
        stmt = stmt.where(Alert.unit.ilike(f"%{unidade}%"))
    if atendimento:
        stmt = stmt.where(Alert.cd_atendimento.ilike(f"%{atendimento}%"))
    if paciente:
        stmt = stmt.where(Alert.patient_name.ilike(f"%{paciente}%"))
    return list(db.scalars(stmt))


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Alert:
    alert = db.scalar(select(Alert).options(selectinload(Alert.actions)).where(Alert.id == alert_id))
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return alert


@router.patch("/{alert_id}/status", response_model=AlertRead)
def patch_status(
    alert_id: int,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Alert:
    if payload.status not in {"ABERTO", "EM_ANALISE", "RESOLVIDO", "IGNORADO"}:
        raise HTTPException(status_code=422, detail="Status inválido")
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return alert_service.change_status(db, alert, payload.status, current_user.id, payload.comment)


@router.post("/{alert_id}/actions", response_model=AlertActionRead)
def add_action(
    alert_id: int,
    payload: AlertActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return alert_service.add_action(db, alert, current_user.id, payload.action, payload.comment)
