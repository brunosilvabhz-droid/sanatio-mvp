from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert, AlertAction
from app.models.user import User
from app.schemas.alert import AlertActionCreate, AlertActionRead, AlertActionReportRead, AlertRead, AlertStatusUpdate
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


@router.get("/actions/report", response_model=list[AlertActionReportRead])
def alert_actions_report(
    status: str | None = None,
    severity: str | None = None,
    atendimento: str | None = None,
    paciente: str | None = None,
    usuario: str | None = None,
    action: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    stmt = (
        select(AlertAction, Alert, User)
        .join(Alert, AlertAction.alert_id == Alert.id)
        .outerjoin(User, AlertAction.user_id == User.id)
        .order_by(AlertAction.created_at.desc())
    )
    if status:
        stmt = stmt.where(Alert.status == status)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if atendimento:
        stmt = stmt.where(Alert.cd_atendimento.ilike(f"%{atendimento}%"))
    if paciente:
        stmt = stmt.where(Alert.patient_name.ilike(f"%{paciente}%"))
    if usuario:
        stmt = stmt.where((User.full_name.ilike(f"%{usuario}%")) | (User.email.ilike(f"%{usuario}%")))
    if action:
        stmt = stmt.where(AlertAction.action.ilike(f"%{action}%"))

    rows = db.execute(stmt).all()
    return [
        {
            "action_id": item.id,
            "alert_id": alert.id,
            "cd_atendimento": alert.cd_atendimento,
            "cd_paciente": alert.cd_paciente,
            "patient_name": alert.patient_name,
            "unit": alert.unit,
            "alert_title": alert.title,
            "alert_status": alert.status,
            "severity": alert.severity,
            "user_id": user.id if user else None,
            "user_name": user.full_name if user else None,
            "user_email": user.email if user else None,
            "action": item.action,
            "comment": item.comment,
            "created_at": item.created_at,
        }
        for item, alert, user in rows
    ]


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
