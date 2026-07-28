from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PatientBedMovement(Base):
    __tablename__ = "patient_bed_movements"
    __table_args__ = (
        UniqueConstraint("cd_atendimento", "moved_at", "to_bed", name="uq_patient_bed_movement_attendance_time_bed"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cd_atendimento: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    cd_paciente: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    moved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    from_unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    from_bed: Mapped[str | None] = mapped_column(String(120), nullable=True)
    to_unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    to_bed: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
