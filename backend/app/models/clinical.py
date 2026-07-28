from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_origem_paciente: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    atendimentos = relationship("Atendimento", back_populates="paciente")


class Atendimento(Base):
    __tablename__ = "atendimentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id"), index=True, nullable=False)
    id_origem_atendimento: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    unidade_atual: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    leito_atual: Mapped[str | None] = mapped_column(String(120), nullable=True)
    data_hora_entrada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_hora_saida: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    paciente = relationship("Paciente", back_populates="atendimentos")
    snapshots = relationship("SnapshotAtendimento", back_populates="atendimento")


class ExecucaoIntegracao(Base):
    __tablename__ = "execucoes_integracao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hospital_integracao_id: Mapped[int | None] = mapped_column(ForeignKey("hospital_integrations.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="EM_EXECUCAO", nullable=False, index=True)
    total_pacientes_recebidos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_snapshots_recebidos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_movimentacoes_recebidas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_alertas_gerados: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mensagem_erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data_hora_fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SnapshotAtendimento(Base):
    __tablename__ = "snapshots_atendimento"
    __table_args__ = (
        UniqueConstraint("atendimento_id", "data_hora_coleta", name="uq_snapshot_atendimento_coleta"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atendimento_id: Mapped[int] = mapped_column(ForeignKey("atendimentos.id"), index=True, nullable=False)
    execucao_integracao_id: Mapped[int | None] = mapped_column(ForeignKey("execucoes_integracao.id"), index=True, nullable=True)
    status_risco: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    dias_internacao: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    possui_cultura_positiva: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    maior_dias_antimicrobiano: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    maior_dias_dispositivo_invasivo: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    possui_isolamento_ativo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_hora_coleta: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    atendimento = relationship("Atendimento", back_populates="snapshots")


class MovimentacaoLeito(Base):
    __tablename__ = "movimentacoes_leito"
    __table_args__ = (
        UniqueConstraint("atendimento_id", "data_hora_movimentacao", "leito_destino", name="uq_movimentacao_leito_atendimento_hora_leito"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atendimento_id: Mapped[int] = mapped_column(ForeignKey("atendimentos.id"), index=True, nullable=False)
    unidade_origem: Mapped[str | None] = mapped_column(String(120), nullable=True)
    leito_origem: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unidade_destino: Mapped[str | None] = mapped_column(String(120), nullable=True)
    leito_destino: Mapped[str | None] = mapped_column(String(120), nullable=True)
    data_hora_movimentacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
