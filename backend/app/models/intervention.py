from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InterventionRequest(Base):
    __tablename__ = "intervention_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cd_atendimento: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    cd_paciente: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="ENVIADA", index=True, nullable=False)
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    responded_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    response: Mapped[str | None] = mapped_column(String(40), nullable=True)
    response_justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    responded_by = relationship("User", foreign_keys=[responded_by_user_id])
    recipients = relationship("InterventionRecipient", back_populates="intervention", cascade="all, delete-orphan")


class InterventionRecipient(Base):
    __tablename__ = "intervention_recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intervention_id: Mapped[int] = mapped_column(ForeignKey("intervention_requests.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="ENVIADO", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    intervention = relationship("InterventionRequest", back_populates="recipients")
    user = relationship("User")
