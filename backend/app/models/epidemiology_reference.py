from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReferenciaEpidemiologica(Base):
    __tablename__ = "referencias_epidemiologicas"
    __table_args__ = (
        UniqueConstraint(
            "codigo_indicador",
            "tipo_unidade",
            "populacao_referencia",
            "regiao",
            "uf",
            "ano_referencia",
            "periodo_referencia",
            "versao_referencia",
            name="uq_referencia_epidemiologica_versao",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_indicador: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    nome_indicador: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    tipo_unidade: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    populacao_referencia: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    regiao: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), index=True, nullable=True)
    ano_referencia: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    periodo_referencia: Mapped[str | None] = mapped_column(String(40), nullable=True)
    p10: Mapped[float | None] = mapped_column(Float, nullable=True)
    p25: Mapped[float | None] = mapped_column(Float, nullable=True)
    p50: Mapped[float | None] = mapped_column(Float, nullable=True)
    p75: Mapped[float | None] = mapped_column(Float, nullable=True)
    p90: Mapped[float | None] = mapped_column(Float, nullable=True)
    unidade_medida: Mapped[str] = mapped_column(String(80), nullable=False)
    fonte: Mapped[str] = mapped_column(String(160), nullable=False)
    descricao_fonte: Mapped[str | None] = mapped_column(Text, nullable=True)
    url_fonte: Mapped[str | None] = mapped_column(Text, nullable=True)
    versao_referencia: Mapped[str] = mapped_column(String(60), nullable=False)
    data_publicacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_importacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ImportacaoReferenciaEpidemiologica(Base):
    __tablename__ = "importacoes_referencias_epidemiologicas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    fonte: Mapped[str] = mapped_column(String(160), nullable=False)
    ano_referencia: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    quantidade_registros: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantidade_erros: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="EM_PROCESSAMENTO", index=True, nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data_hora_fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mensagem_erro: Mapped[str | None] = mapped_column(Text, nullable=True)


class PerfilEstabelecimento(Base):
    __tablename__ = "perfis_estabelecimento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cnes: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    nome_estabelecimento: Mapped[str | None] = mapped_column(String(255), nullable=True)
    municipio: Mapped[str | None] = mapped_column(String(120), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    quantidade_leitos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantidade_leitos_uti: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_ultima_atualizacao_cnes: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fonte: Mapped[str | None] = mapped_column(String(160), nullable=True)
    erro_ultima_atualizacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class FechamentoAnvisa(Base):
    __tablename__ = "fechamentos_anvisa"
    __table_args__ = (
        UniqueConstraint("tipo_unidade", "periodo", name="uq_fechamento_anvisa_tipo_periodo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_unidade: Mapped[str] = mapped_column(String(120), default="UTI_ADULTO", nullable=False, index=True)
    periodo: Mapped[str] = mapped_column(String(7), index=True, nullable=False)
    paciente_dia: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cvc_dia: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vm_dia: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cvd_dia: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    casos_ipcsl: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    casos_pav: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    casos_itu_cvd: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    densidade_ipcsl: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    densidade_pav: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    densidade_itu_cvd: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="rascunho", index=True, nullable=False)
    validado_por: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    data_hora_validacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acao: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    registro: Mapped[str] = mapped_column(String(255), nullable=False)
    valor_anterior: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_novo: Mapped[str | None] = mapped_column(Text, nullable=True)
