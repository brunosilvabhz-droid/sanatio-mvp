from datetime import datetime

from pydantic import BaseModel


class MonitoringRuleCreate(BaseModel):
    name: str
    description: str | None = None
    rule_type: str
    parameter_key: str
    parameter_value: str
    severity: str
    active: bool = True


class MonitoringRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    rule_type: str | None = None
    parameter_key: str | None = None
    parameter_value: str | None = None
    severity: str | None = None
    active: bool | None = None


class MonitoringRuleRead(BaseModel):
    id: int
    name: str
    description: str | None
    rule_type: str
    parameter_key: str
    parameter_value: str
    severity: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
