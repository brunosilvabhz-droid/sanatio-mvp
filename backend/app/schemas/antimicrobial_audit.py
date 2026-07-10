from datetime import datetime

from pydantic import BaseModel


class AntimicrobialAuditActionRead(BaseModel):
    id: int
    audit_id: int
    user_id: int | None
    user_name: str | None = None
    action: str
    status: str | None
    decision: str | None
    comment: str | None
    created_at: datetime


class AntimicrobialAuditRead(BaseModel):
    id: int
    cd_atendimento: str
    cd_paciente: str
    unit: str | None
    cd_prescricao: str
    cd_item_prescricao: str
    cd_produto: str | None
    antimicrobial_name: str
    started_at: datetime
    ended_at: datetime | None
    days_in_use: int
    active: bool
    dose: str | None
    route: str | None
    frequency: str | None
    status: str
    priority: str
    decision: str | None
    justification: str | None
    reviewed_by_user_id: int | None
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    actions: list[AntimicrobialAuditActionRead] = []


class AntimicrobialAuditUpdate(BaseModel):
    status: str
    decision: str | None = None
    comment: str
