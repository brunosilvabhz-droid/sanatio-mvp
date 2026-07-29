from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.clinical import ExecucaoIntegracao
from app.models.hospital_integration import HospitalIntegration
from app.models.monitoring_run import MonitoringRun
from app.models.monitoring_rule import MonitoringRule
from app.models.setting import Setting
from app.models.user import User
from app.schemas.monitoring_run import MonitoringRunRead
from app.schemas.monitoring_rule import MonitoringRuleCreate, MonitoringRuleRead, MonitoringRuleUpdate
from app.schemas.monitoring_schedule import MonitoringScheduleRead, MonitoringScheduleUpdate

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
        source_key=f"monitoring-{run.id}",
        source_type="Monitoramento manual",
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


def _integration_run_to_read(run: ExecucaoIntegracao, hospital_name: str | None) -> MonitoringRunRead:
    duration_ms = None
    if run.data_hora_fim:
        duration_ms = int((run.data_hora_fim - run.data_hora_inicio).total_seconds() * 1000)
    return MonitoringRunRead(
        source_key=f"integration-{run.id}",
        source_type="Integracao hospitalar",
        id=run.id,
        triggered_by_user_id=None,
        triggered_by_name=hospital_name or "Hospital",
        triggered_by_email=None,
        status=run.status,
        patients_processed=run.total_snapshots_recebidos,
        alerts_created=run.total_alertas_gerados,
        duration_ms=duration_ms,
        error_message=run.mensagem_erro,
        started_at=run.data_hora_inicio,
        finished_at=run.data_hora_fim,
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
    monitoring_runs = db.scalars(
        select(MonitoringRun)
        .options(selectinload(MonitoringRun.triggered_by))
        .order_by(MonitoringRun.started_at.desc())
        .limit(100)
    ).all()
    integration_runs = db.scalars(select(ExecucaoIntegracao).order_by(ExecucaoIntegracao.data_hora_inicio.desc()).limit(100)).all()
    hospital_ids = {run.hospital_integracao_id for run in integration_runs if run.hospital_integracao_id}
    hospitals = {}
    if hospital_ids:
        hospitals = {
            hospital.id: hospital.hospital_name
            for hospital in db.scalars(select(HospitalIntegration).where(HospitalIntegration.id.in_(hospital_ids))).all()
        }
    runs = [_run_to_read(run) for run in monitoring_runs]
    runs.extend(_integration_run_to_read(run, hospitals.get(run.hospital_integracao_id)) for run in integration_runs)
    return sorted(runs, key=lambda run: run.started_at, reverse=True)[:100]
