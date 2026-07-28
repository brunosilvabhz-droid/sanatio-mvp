"""patient history ingestion

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("patient_monitoring_snapshots", sa.Column("bed", sa.String(length=120), nullable=True))
    op.add_column("patient_monitoring_snapshots", sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("patient_monitoring_snapshots", sa.Column("admitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("patient_monitoring_snapshots", sa.Column("discharged_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_patient_monitoring_snapshots_active"), "patient_monitoring_snapshots", ["active"], unique=False)

    op.create_table(
        "patient_bed_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cd_atendimento", sa.String(length=60), nullable=False),
        sa.Column("cd_paciente", sa.String(length=60), nullable=False),
        sa.Column("moved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("from_unit", sa.String(length=120), nullable=True),
        sa.Column("from_bed", sa.String(length=120), nullable=True),
        sa.Column("to_unit", sa.String(length=120), nullable=True),
        sa.Column("to_bed", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cd_atendimento", "moved_at", "to_bed", name="uq_patient_bed_movement_attendance_time_bed"),
    )
    op.create_index(op.f("ix_patient_bed_movements_cd_atendimento"), "patient_bed_movements", ["cd_atendimento"], unique=False)
    op.create_index(op.f("ix_patient_bed_movements_cd_paciente"), "patient_bed_movements", ["cd_paciente"], unique=False)
    op.create_index(op.f("ix_patient_bed_movements_moved_at"), "patient_bed_movements", ["moved_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_patient_bed_movements_moved_at"), table_name="patient_bed_movements")
    op.drop_index(op.f("ix_patient_bed_movements_cd_paciente"), table_name="patient_bed_movements")
    op.drop_index(op.f("ix_patient_bed_movements_cd_atendimento"), table_name="patient_bed_movements")
    op.drop_table("patient_bed_movements")
    op.drop_index(op.f("ix_patient_monitoring_snapshots_active"), table_name="patient_monitoring_snapshots")
    op.drop_column("patient_monitoring_snapshots", "discharged_at")
    op.drop_column("patient_monitoring_snapshots", "admitted_at")
    op.drop_column("patient_monitoring_snapshots", "active")
    op.drop_column("patient_monitoring_snapshots", "bed")
