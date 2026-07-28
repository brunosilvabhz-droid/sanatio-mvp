from datetime import datetime

from pydantic import BaseModel


class HospitalIntegrationCreate(BaseModel):
    hospital_name: str


class HospitalIntegrationRead(BaseModel):
    id: int
    hospital_name: str
    token: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IngestPatientSnapshot(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    unit: str | None = None
    bed: str | None = None
    active: bool = True
    admitted_at: datetime | None = None
    discharged_at: datetime | None = None
    risk_status: str
    days_in_hospital: int = 0
    has_positive_culture: bool = False
    max_antimicrobial_days: int = 0
    max_invasive_device_days: int = 0
    has_active_isolation: bool = False


class IngestBedMovement(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    moved_at: datetime
    from_unit: str | None = None
    from_bed: str | None = None
    to_unit: str | None = None
    to_bed: str | None = None


class IngestPayload(BaseModel):
    patients: list[IngestPatientSnapshot]
    bed_movements: list[IngestBedMovement] = []
