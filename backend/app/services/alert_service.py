from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertAction

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
    return alert


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
