from datetime import datetime

from pydantic import BaseModel


class SupportTicketCreate(BaseModel):
    category: str
    title: str
    description: str


class SupportTicketUpdate(BaseModel):
    status: str
    admin_response: str | None = None


class SupportTicketRead(BaseModel):
    id: int
    category: str
    title: str
    description: str
    status: str
    requester_user_id: int
    requester_name: str | None = None
    requester_email: str | None = None
    responder_user_id: int | None = None
    responder_name: str | None = None
    admin_response: str | None = None
    created_at: datetime
    updated_at: datetime
    responded_at: datetime | None = None
