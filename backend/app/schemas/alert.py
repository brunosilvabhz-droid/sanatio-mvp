from datetime import datetime

from pydantic import BaseModel


class AlertActionCreate(BaseModel):
    action: str = "COMMENT"
    comment: str | None = None


class AlertStatusUpdate(BaseModel):
    status: str
    comment: str | None = None


class AlertActionRead(BaseModel):
    id: int
    alert_id: int
    user_id: int | None
    action: str
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertRead(BaseModel):
    id: int
    cd_atendimento: str
    cd_paciente: str
    patient_name: str | None
    unit: str | None
    rule_id: int | None
    alert_type: str
    severity: str
    title: str
    description: str
    recommendation: str | None
    status: str
    source: str
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    actions: list[AlertActionRead] = []

    model_config = {"from_attributes": True}


class AlertActionReportRead(BaseModel):
    action_id: int
    alert_id: int
    cd_atendimento: str
    cd_paciente: str
    patient_name: str | None
    unit: str | None
    alert_title: str
    alert_status: str
    severity: str
    user_id: int | None
    user_name: str | None
    user_email: str | None
    action: str
    comment: str | None
    created_at: datetime
