from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ImportacaoPdfLaboratorio(Base):
    __tablename__ = "importacoes_pdf_laboratorio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    paginas: Mapped[int] = mapped_column(Integer, nullable=False)
    total_resultados: Mapped[int] = mapped_column(Integer, nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    importado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resultados = relationship("ResultadoPdfLaboratorio", back_populates="importacao")


class ResultadoPdfLaboratorio(Base):
    __tablename__ = "resultados_pdf_laboratorio"
    __table_args__ = (UniqueConstraint("importacao_id", "ordem", name="uq_resultado_pdf_importacao_ordem"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    importacao_id: Mapped[int] = mapped_column(ForeignKey("importacoes_pdf_laboratorio.id"), nullable=False, index=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    pagina: Mapped[int] = mapped_column(Integer, nullable=False)
    os_pedido: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    nome_relatorio: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_coleta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_resultado: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exame_amostra: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[str] = mapped_column(Text, nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), nullable=False)
    atendimento_sugerido_id: Mapped[int | None] = mapped_column(ForeignKey("atendimentos.id"), nullable=True)
    atendimento_id: Mapped[int | None] = mapped_column(ForeignKey("atendimentos.id"), nullable=True, index=True)
    vinculado_por_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    vinculado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    importacao = relationship("ImportacaoPdfLaboratorio", back_populates="resultados")
