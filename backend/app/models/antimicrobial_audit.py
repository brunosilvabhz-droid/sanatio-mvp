from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AntimicrobialAudit(Base):
    __tablename__ = "antimicrobial_audits"
    __table_args__ = (UniqueConstraint("cd_prescricao", "cd_item_prescricao", name="uq_antimicrobial_audit_prescription_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    monitoring_run_id: Mapped[int | None] = mapped_column(ForeignKey("monitoring_runs.id"), nullable=True, index=True)
    cd_atendimento: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    cd_paciente: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(120), index=True)
    cd_prescricao: Mapped[str] = mapped_column(String(60), nullable=False)
    cd_item_prescricao: Mapped[str] = mapped_column(String(60), nullable=False)
    cd_produto: Mapped[str | None] = mapped_column(String(60), nullable=True)
    antimicrobial_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    days_in_use: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    dose: Mapped[str | None] = mapped_column(String(120), nullable=True)
    route: Mapped[str | None] = mapped_column(String(80), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="PENDENTE", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(40), default="MEDIA", nullable=False, index=True)
    decision: Mapped[str | None] = mapped_column(String(80), nullable=True)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    monitoring_run = relationship("MonitoringRun")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])
    actions = relationship("AntimicrobialAuditAction", back_populates="audit", cascade="all, delete-orphan")


class AntimicrobialAuditAction(Base):
    __tablename__ = "antimicrobial_audit_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(ForeignKey("antimicrobial_audits.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(80), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    audit = relationship("AntimicrobialAudit", back_populates="actions")
    user = relationship("User")
