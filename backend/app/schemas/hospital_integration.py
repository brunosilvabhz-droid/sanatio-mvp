from datetime import datetime

from pydantic import BaseModel


class HospitalIntegrationCreate(BaseModel):
    hospital_name: str


class HospitalIntegrationRead(BaseModel):
    id: int
    hospital_name: str
    token: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IngestPatientSnapshot(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    unit: str | None = None
    risk_status: str
    days_in_hospital: int = 0
    has_positive_culture: bool = False
    max_antimicrobial_days: int = 0
    max_invasive_device_days: int = 0
    has_active_isolation: bool = False


class IngestPayload(BaseModel):
    patients: list[IngestPatientSnapshot]
