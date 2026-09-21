from datetime import datetime

from pydantic import BaseModel


class ReferenciaEpidemiologicaBase(BaseModel):
    codigo_indicador: str
    nome_indicador: str
    tipo_unidade: str
    populacao_referencia: str
    regiao: str | None = None
    uf: str | None = None
    ano_referencia: int
    periodo_referencia: str | None = None
    p10: float | None = None
    p25: float | None = None
    p50: float | None = None
    p75: float | None = None
    p90: float | None = None
    unidade_medida: str
    fonte: str
    descricao_fonte: str | None = None
    url_fonte: str | None = None
    versao_referencia: str
    data_publicacao: datetime | None = None
    ativo: bool = True


class ReferenciaEpidemiologicaCreate(ReferenciaEpidemiologicaBase):
    pass


class ReferenciaEpidemiologicaRead(ReferenciaEpidemiologicaBase):
    id: int
    data_importacao: datetime
    data_criacao: datetime
    data_atualizacao: datetime

    model_config = {"from_attributes": True}


class ImportacaoReferenciaRead(BaseModel):
    id: int
    nome_arquivo: str
    fonte: str
    ano_referencia: int | None
    quantidade_registros: int
    quantidade_erros: int
    status: str
    usuario_id: int | None
    data_hora_inicio: datetime
    data_hora_fim: datetime | None
    mensagem_erro: str | None

    model_config = {"from_attributes": True}


class BenchmarkHistoricoRead(BaseModel):
    mes: str
    valor: float
    p50: float | None = None
    p75: float | None = None


class BenchmarkComparacaoRead(BaseModel):
    indicador: str
    codigo_indicador: str
    valor_hospital: float
    numerador: int
    denominador: int
    unidade_medida: str
    benchmark_utilizado: int | None
    p10: float | None = None
    p25: float | None = None
    p50: float | None = None
    p75: float | None = None
    p90: float | None = None
    faixa_estatistica: str
    periodo_referencia: str
    ano_referencia: int | None = None
    fonte: str | None = None
    url_fonte: str | None = None
    historico: list[BenchmarkHistoricoRead]


class PerfilEstabelecimentoRead(BaseModel):
    id: int
    cnes: str
    nome_estabelecimento: str | None
    municipio: str | None
    uf: str | None
    quantidade_leitos: int | None
    quantidade_leitos_uti: int | None
    data_ultima_atualizacao_cnes: datetime | None
    fonte: str | None
    erro_ultima_atualizacao: str | None

    model_config = {"from_attributes": True}


class PerfilEstabelecimentoUpdate(BaseModel):
    cnes: str
    nome_estabelecimento: str | None = None
    municipio: str | None = None
    uf: str | None = None
    quantidade_leitos: int | None = None
    quantidade_leitos_uti: int | None = None


class FechamentoAnvisaRead(BaseModel):
    id: int
    tipo_unidade: str
    periodo: str
    paciente_dia: int
    cvc_dia: int
    vm_dia: int
    cvd_dia: int
    casos_ipcsl: int
    casos_pav: int
    casos_itu_cvd: int
    densidade_ipcsl: float
    densidade_pav: float
    densidade_itu_cvd: float
    status: str
    validado_por: int | None
    data_hora_validacao: datetime | None

    model_config = {"from_attributes": True}


class FechamentoStatusUpdate(BaseModel):
    status: str
