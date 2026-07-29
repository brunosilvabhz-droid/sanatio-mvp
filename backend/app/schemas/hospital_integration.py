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


class IngestAntimicrobial(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    cd_prescricao: str
    cd_item_prescricao: str
    cd_produto: str | None = None
    ds_antimicrobiano: str
    ds_principio_ativo: str | None = None
    dt_inicio: datetime
    dt_fim: datetime | None = None
    sn_ativo: str = "S"
    ds_frequencia: str | None = None
    ds_via: str | None = None
    ds_dose: str | None = None
    dias_uso: int = 0


class IngestCulture(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    cd_pedido: str
    cd_exame: str
    ds_exame: str
    dt_coleta: datetime
    dt_resultado: datetime | None = None
    ds_material: str | None = None
    ds_microorganismo: str | None = None
    ds_resultado: str | None = None
    sn_positivo: str = "N"


class IngestInvasiveProcedure(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    cd_procedimento: str
    ds_procedimento: str
    dt_inicio: datetime
    dt_fim: datetime | None = None
    sn_ativo: str = "S"
    ds_local_instalacao: str | None = None
    dias_permanencia: int = 0


class IngestIsolation(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    cd_isolamento: str
    ds_isolamento: str
    dt_inicio: datetime
    dt_fim: datetime | None = None
    sn_ativo: str = "S"


class IngestPayload(BaseModel):
    patients: list[IngestPatientSnapshot]
    bed_movements: list[IngestBedMovement] = []
    antimicrobials: list[IngestAntimicrobial] = []
    cultures: list[IngestCulture] = []
    invasive_procedures: list[IngestInvasiveProcedure] = []
    isolations: list[IngestIsolation] = []
