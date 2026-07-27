"""monitoring run history

Revision ID: 0004
Revises: 0003_patient_name_privacy
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monitoring_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("triggered_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("patients_processed", sa.Integer(), nullable=False),
        sa.Column("alerts_created", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["triggered_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_runs_status", "monitoring_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_monitoring_runs_status", table_name="monitoring_runs")
    op.drop_table("monitoring_runs")
