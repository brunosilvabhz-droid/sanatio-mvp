from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PatientMonitoringSnapshot(Base):
    __tablename__ = "patient_monitoring_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    monitoring_run_id: Mapped[int | None] = mapped_column(ForeignKey("monitoring_runs.id"), nullable=True, index=True)
    cd_atendimento: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    cd_paciente: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(120), index=True)
    risk_status: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    days_in_hospital: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_positive_culture: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_antimicrobial_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_invasive_device_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_active_isolation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    monitoring_run = relationship("MonitoringRun")
