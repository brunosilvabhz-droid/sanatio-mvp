from datetime import date, datetime

from pydantic import BaseModel


class Patient(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    nm_paciente: str | None = None
    dt_nascimento: date
    tp_sexo: str
    dt_atendimento: datetime
    cd_unidade: str
    ds_unidade: str
    cd_leito: str
    ds_leito: str
    active: bool = True
    discharged_at: datetime | None = None
    cd_prestador: str
    nm_prestador: str
    cd_convenio: str
    nm_convenio: str
    idade: int
    dias_internacao: int
    status_risco: str
    risk_reasons: list[str] = []


class Antimicrobial(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    cd_prescricao: str
    cd_item_prescricao: str
    cd_produto: str
    ds_antimicrobiano: str
    ds_principio_ativo: str
    dt_inicio: datetime
    dt_aplicacao: datetime | None = None
    dt_fim: datetime | None = None
    sn_ativo: str
    ds_frequencia: str
    ds_via: str
    ds_dose: str
    dias_uso: int


class Culture(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    cd_pedido: str
    cd_exame: str
    ds_exame: str
    dt_coleta: datetime
    dt_resultado: datetime | None = None
    ds_material: str
    ds_microorganismo: str | None = None
    ds_resultado: str
    sn_positivo: str


class InvasiveProcedure(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    cd_procedimento: str
    ds_procedimento: str
    dt_inicio: datetime
    dt_fim: datetime | None = None
    sn_ativo: str
    ds_local_instalacao: str
    dias_permanencia: int


class Isolation(BaseModel):
    cd_atendimento: str
    cd_paciente: str
    cd_isolamento: str
    ds_isolamento: str
    dt_inicio: datetime
    dt_fim: datetime | None = None
    sn_ativo: str


class PatientDetail(BaseModel):
    patient: Patient
    antimicrobials: list[Antimicrobial]
    cultures: list[Culture]
    invasive_procedures: list[InvasiveProcedure]
    isolations: list[Isolation]
