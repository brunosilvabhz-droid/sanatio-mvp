from datetime import datetime

from pydantic import BaseModel


class RecipientRead(BaseModel):
    id: int
    email: str
    full_name: str
    role_name: str


class InterventionCreate(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    source_type: str
    source_id: int | None = None
    reason: str
    message: str
    recipient_user_ids: list[int]


class InterventionResponseUpdate(BaseModel):
    response: str
    justification: str


class InterventionRecipientRead(BaseModel):
    id: int
    user_id: int
    email: str
    user_name: str | None = None
    status: str
    created_at: datetime


class InterventionRead(BaseModel):
    id: int
    cd_atendimento: str
    cd_paciente: str
    source_type: str
    source_id: int | None
    reason: str
    message: str
    status: str
    requested_by_user_id: int | None
    requested_by_name: str | None = None
    responded_by_user_id: int | None
    responded_by_name: str | None = None
    response: str | None
    response_justification: str | None
    created_at: datetime
    responded_at: datetime | None
    updated_at: datetime
    recipients: list[InterventionRecipientRead] = []


class TimelineEventRead(BaseModel):
    id: str
    type: str
    title: str
    description: str | None = None
    status: str | None = None
    actor: str | None = None
    created_at: datetime


class PatientTimelineNoteCreate(BaseModel):
    cd_paciente: str
    note: str
    note_type: str = "EVOLUCAO"
