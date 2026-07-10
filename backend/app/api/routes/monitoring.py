from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.monitoring_run import MonitoringRun
from app.models.monitoring_rule import MonitoringRule
from app.models.setting import Setting
from app.models.user import User
from app.schemas.monitoring_run import MonitoringRunRead, MonitoringRunResult
from app.schemas.monitoring_rule import MonitoringRuleCreate, MonitoringRuleRead, MonitoringRuleUpdate
from app.schemas.monitoring_schedule import MonitoringScheduleRead, MonitoringScheduleUpdate
from app.services.monitoring_service import run_monitoring

router = APIRouter(prefix="/monitoring", tags=["Monitoramento"])

SCHEDULE_SETTINGS = {
    "enabled": ("monitoring.schedule.enabled", "false", "Ativa a execucao automatica do monitoramento"),
    "interval_minutes": ("monitoring.schedule.interval_minutes", "60", "Intervalo entre execucoes automaticas em minutos"),
    "daily_time": ("monitoring.schedule.daily_time", "07:00", "Horario preferencial de execucao diaria"),
    "timezone": ("monitoring.schedule.timezone", "America/Sao_Paulo", "Fuso horario da agenda automatica"),
}


def _run_to_read(run: MonitoringRun) -> MonitoringRunRead:
    user = run.triggered_by
    return MonitoringRunRead(
        id=run.id,
        triggered_by_user_id=run.triggered_by_user_id,
        triggered_by_name=user.full_name if user else None,
        triggered_by_email=user.email if user else None,
        status=run.status,
        patients_processed=run.patients_processed,
        alerts_created=run.alerts_created,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )


def _get_setting(db: Session, key: str, default: str, description: str) -> Setting:
    setting = db.scalar(select(Setting).where(Setting.key == key))
    if not setting:
        setting = Setting(key=key, value=default, description=description)
        db.add(setting)
        db.flush()
    return setting


def _schedule_from_settings(db: Session) -> MonitoringScheduleRead:
    values = {}
    for field, (key, default, description) in SCHEDULE_SETTINGS.items():
        values[field] = _get_setting(db, key, default, description).value or default
    db.commit()
    return MonitoringScheduleRead(
        enabled=str(values["enabled"]).lower() == "true",
        interval_minutes=int(values["interval_minutes"]),
        daily_time=values["daily_time"],
        timezone=values["timezone"],
    )


@router.get("/rules", response_model=list[MonitoringRuleRead])
def list_rules(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[MonitoringRule]:
    return list(db.scalars(select(MonitoringRule).order_by(MonitoringRule.active.desc(), MonitoringRule.name)))


@router.post("/rules", response_model=MonitoringRuleRead)
def create_rule(payload: MonitoringRuleCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> MonitoringRule:
    rule = MonitoringRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/rules/{rule_id}", response_model=MonitoringRuleRead)
def update_rule(
    rule_id: int,
    payload: MonitoringRuleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MonitoringRule:
    rule = db.get(MonitoringRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/schedule", response_model=MonitoringScheduleRead)
def get_schedule(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> MonitoringScheduleRead:
    return _schedule_from_settings(db)


@router.patch("/schedule", response_model=MonitoringScheduleRead)
def update_schedule(
    payload: MonitoringScheduleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MonitoringScheduleRead:
    if len(payload.daily_time) != 5 or payload.daily_time[2] != ":":
        raise HTTPException(status_code=422, detail="Horario deve estar no formato HH:MM")
    hour, minute = payload.daily_time.split(":")
    if not (hour.isdigit() and minute.isdigit() and 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
        raise HTTPException(status_code=422, detail="Horario invalido")

    values = {
        "enabled": "true" if payload.enabled else "false",
        "interval_minutes": str(payload.interval_minutes),
        "daily_time": payload.daily_time,
        "timezone": payload.timezone,
    }
    for field, value in values.items():
        key, default, description = SCHEDULE_SETTINGS[field]
        setting = _get_setting(db, key, default, description)
        setting.value = value
        setting.description = description
    db.commit()
    return _schedule_from_settings(db)


@router.get("/runs", response_model=list[MonitoringRunRead])
def list_runs(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[MonitoringRunRead]:
    runs = db.scalars(
        select(MonitoringRun)
        .options(selectinload(MonitoringRun.triggered_by))
        .order_by(MonitoringRun.started_at.desc())
        .limit(100)
    )
    return [_run_to_read(run) for run in runs]


@router.post("/run", response_model=MonitoringRunResult)
def run(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> MonitoringRunResult:
    started_at = datetime.now(timezone.utc)
    monitoring_run = MonitoringRun(triggered_by_user_id=current_user.id, status="RUNNING", started_at=started_at)
    db.add(monitoring_run)
    db.commit()
    db.refresh(monitoring_run)
    run_id = monitoring_run.id

    try:
        result = run_monitoring(db, monitoring_run_id=run_id)
    except Exception as exc:
        db.rollback()
        finished_at = datetime.now(timezone.utc)
        monitoring_run = db.get(MonitoringRun, run_id)
        if monitoring_run:
            monitoring_run.status = "FAILED"
            monitoring_run.finished_at = finished_at
            monitoring_run.duration_ms = int((finished_at - started_at).total_seconds() * 1000)
            monitoring_run.error_message = str(exc)[:4000]
            db.commit()
        raise HTTPException(status_code=500, detail="Falha ao executar monitoramento") from exc

    finished_at = datetime.now(timezone.utc)
    monitoring_run = db.get(MonitoringRun, run_id)
    if monitoring_run:
        monitoring_run.status = "SUCCESS"
        monitoring_run.patients_processed = int(result.get("patients_processed", 0))
        monitoring_run.alerts_created = int(result.get("alerts_created", 0))
        monitoring_run.finished_at = finished_at
        monitoring_run.duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        db.commit()

    return MonitoringRunResult(run_id=run_id, status="SUCCESS", **result)
