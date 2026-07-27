from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PatientTimelineNote(Base):
    __tablename__ = "patient_timeline_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cd_atendimento: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    cd_paciente: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    note_type: Mapped[str] = mapped_column(String(40), default="EVOLUCAO", nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
