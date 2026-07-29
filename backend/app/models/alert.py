from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cd_atendimento: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    cd_paciente: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(120), index=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("monitoring_rules.id"))
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), index=True, default="ABERTO", nullable=False)
    source: Mapped[str] = mapped_column(String(80), default="monitoring", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rule = relationship("MonitoringRule")
    actions = relationship("AlertAction", back_populates="alert", cascade="all, delete-orphan")


class AlertAction(Base):
    __tablename__ = "alert_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alert = relationship("Alert", back_populates="actions")
    user = relationship("User")
