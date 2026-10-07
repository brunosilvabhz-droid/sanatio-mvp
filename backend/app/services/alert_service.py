from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import Alert, AlertAction
from app.models.user import Role, User
from app.services.email_service import send_email

OPEN_STATUSES = ["ABERTO", "EM_ANALISE"]


def create_alert_if_missing(db: Session, payload: dict) -> Alert | None:
    existing = db.scalar(
        select(Alert).where(
            Alert.cd_atendimento == payload["cd_atendimento"],
            Alert.rule_id == payload.get("rule_id"),
            Alert.status.in_(OPEN_STATUSES),
        )
    )
    if existing:
        return None
    alert = Alert(**payload)
    db.add(alert)
    db.flush()
    notify_alert_created(db, alert)
    return alert


def notify_alert_created(db: Session, alert: Alert) -> bool:
    if not settings.alert_email_enabled:
        return False

    recipients = set(settings.alert_notification_email_list)
    if settings.alert_notification_role_list:
        recipients.update(
            db.scalars(
                select(User.email)
                .join(Role, User.role_id == Role.id)
                .where(User.active.is_(True), Role.name.in_(settings.alert_notification_role_list))
            )
        )
    recipients = {email for email in recipients if not email.lower().endswith("@sanatio.local")}
    if not recipients:
        return False

    alert_url = f"{settings.app_public_url.rstrip('/')}/alerts"
    return send_email(
        to=sorted(recipients),
        subject=f"SANATIO | Novo alerta {alert.severity}: {alert.title}",
        body=(
            "Um novo alerta assistencial foi identificado pelo SANATIO.\n\n"
            f"Atendimento: {alert.cd_atendimento}\n"
            f"Paciente ID: {alert.cd_paciente}\n"
            f"Unidade: {alert.unit or 'Não informada'}\n"
            f"Severidade: {alert.severity}\n"
            f"Alerta: {alert.title}\n"
            f"Descrição: {alert.description}\n\n"
            f"Acessar alertas: {alert_url}\n\n"
            "Por segurança, o nome do paciente não é enviado por e-mail."
        ),
    )


def change_status(db: Session, alert: Alert, status: str, user_id: int | None, comment: str | None = None) -> Alert:
    alert.status = status
    alert.updated_at = datetime.now(timezone.utc)
    alert.resolved_at = datetime.now(timezone.utc) if status in {"RESOLVIDO", "IGNORADO"} else None
    db.add(AlertAction(alert_id=alert.id, user_id=user_id, action=f"STATUS_{status}", comment=comment))
    db.commit()
    db.refresh(alert)
    return alert


def add_action(db: Session, alert: Alert, user_id: int | None, action: str, comment: str | None) -> AlertAction:
    item = AlertAction(alert_id=alert.id, user_id=user_id, action=action, comment=comment)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
