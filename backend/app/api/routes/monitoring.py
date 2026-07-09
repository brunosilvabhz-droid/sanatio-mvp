from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.monitoring_rule import MonitoringRule
from app.schemas.monitoring_rule import MonitoringRuleCreate, MonitoringRuleRead, MonitoringRuleUpdate
from app.services.monitoring_service import run_monitoring

router = APIRouter(prefix="/monitoring", tags=["Monitoramento"], dependencies=[Depends(get_current_user)])


@router.get("/rules", response_model=list[MonitoringRuleRead])
def list_rules(db: Session = Depends(get_db)) -> list[MonitoringRule]:
    return list(db.scalars(select(MonitoringRule).order_by(MonitoringRule.active.desc(), MonitoringRule.name)))


@router.post("/rules", response_model=MonitoringRuleRead)
def create_rule(payload: MonitoringRuleCreate, db: Session = Depends(get_db)) -> MonitoringRule:
    rule = MonitoringRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/rules/{rule_id}", response_model=MonitoringRuleRead)
def update_rule(rule_id: int, payload: MonitoringRuleUpdate, db: Session = Depends(get_db)) -> MonitoringRule:
    rule = db.get(MonitoringRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/run")
def run(db: Session = Depends(get_db)) -> dict:
    return run_monitoring(db)
