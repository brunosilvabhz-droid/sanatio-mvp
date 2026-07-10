"""patient monitoring snapshots

Revision ID: 0005_patient_monitoring_snapshots
Revises: 0004_monitoring_runs
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_patient_monitoring_snapshots"
down_revision = "0004_monitoring_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_monitoring_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("monitoring_run_id", sa.Integer(), nullable=True),
        sa.Column("cd_atendimento", sa.String(length=60), nullable=False),
        sa.Column("cd_paciente", sa.String(length=60), nullable=False),
        sa.Column("unit", sa.String(length=120), nullable=True),
        sa.Column("risk_status", sa.String(length=40), nullable=False),
        sa.Column("days_in_hospital", sa.Integer(), nullable=False),
        sa.Column("has_positive_culture", sa.Boolean(), nullable=False),
        sa.Column("max_antimicrobial_days", sa.Integer(), nullable=False),
        sa.Column("max_invasive_device_days", sa.Integer(), nullable=False),
        sa.Column("has_active_isolation", sa.Boolean(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["monitoring_run_id"], ["monitoring_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patient_monitoring_snapshots_monitoring_run_id", "patient_monitoring_snapshots", ["monitoring_run_id"])
    op.create_index("ix_patient_monitoring_snapshots_cd_atendimento", "patient_monitoring_snapshots", ["cd_atendimento"])
    op.create_index("ix_patient_monitoring_snapshots_cd_paciente", "patient_monitoring_snapshots", ["cd_paciente"])
    op.create_index("ix_patient_monitoring_snapshots_unit", "patient_monitoring_snapshots", ["unit"])
    op.create_index("ix_patient_monitoring_snapshots_risk_status", "patient_monitoring_snapshots", ["risk_status"])


def downgrade() -> None:
    op.drop_index("ix_patient_monitoring_snapshots_risk_status", table_name="patient_monitoring_snapshots")
    op.drop_index("ix_patient_monitoring_snapshots_unit", table_name="patient_monitoring_snapshots")
    op.drop_index("ix_patient_monitoring_snapshots_cd_paciente", table_name="patient_monitoring_snapshots")
    op.drop_index("ix_patient_monitoring_snapshots_cd_atendimento", table_name="patient_monitoring_snapshots")
    op.drop_index("ix_patient_monitoring_snapshots_monitoring_run_id", table_name="patient_monitoring_snapshots")
    op.drop_table("patient_monitoring_snapshots")
