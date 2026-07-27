"""antimicrobial audits

Revision ID: 0007
Revises: 0006_internal_rule_fields
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "antimicrobial_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("monitoring_run_id", sa.Integer(), nullable=True),
        sa.Column("cd_atendimento", sa.String(length=60), nullable=False),
        sa.Column("cd_paciente", sa.String(length=60), nullable=False),
        sa.Column("unit", sa.String(length=120), nullable=True),
        sa.Column("cd_prescricao", sa.String(length=60), nullable=False),
        sa.Column("cd_item_prescricao", sa.String(length=60), nullable=False),
        sa.Column("cd_produto", sa.String(length=60), nullable=True),
        sa.Column("antimicrobial_name", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("days_in_use", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("dose", sa.String(length=120), nullable=True),
        sa.Column("route", sa.String(length=80), nullable=True),
        sa.Column("frequency", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("priority", sa.String(length=40), nullable=False),
        sa.Column("decision", sa.String(length=80), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["monitoring_run_id"], ["monitoring_runs.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cd_prescricao", "cd_item_prescricao", name="uq_antimicrobial_audit_prescription_item"),
    )
    op.create_index("ix_antimicrobial_audits_monitoring_run_id", "antimicrobial_audits", ["monitoring_run_id"])
    op.create_index("ix_antimicrobial_audits_cd_atendimento", "antimicrobial_audits", ["cd_atendimento"])
    op.create_index("ix_antimicrobial_audits_cd_paciente", "antimicrobial_audits", ["cd_paciente"])
    op.create_index("ix_antimicrobial_audits_unit", "antimicrobial_audits", ["unit"])
    op.create_index("ix_antimicrobial_audits_antimicrobial_name", "antimicrobial_audits", ["antimicrobial_name"])
    op.create_index("ix_antimicrobial_audits_active", "antimicrobial_audits", ["active"])
    op.create_index("ix_antimicrobial_audits_status", "antimicrobial_audits", ["status"])
    op.create_index("ix_antimicrobial_audits_priority", "antimicrobial_audits", ["priority"])

    op.create_table(
        "antimicrobial_audit_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=True),
        sa.Column("decision", sa.String(length=80), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["audit_id"], ["antimicrobial_audits.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("antimicrobial_audit_actions")
    op.drop_index("ix_antimicrobial_audits_priority", table_name="antimicrobial_audits")
    op.drop_index("ix_antimicrobial_audits_status", table_name="antimicrobial_audits")
    op.drop_index("ix_antimicrobial_audits_active", table_name="antimicrobial_audits")
    op.drop_index("ix_antimicrobial_audits_antimicrobial_name", table_name="antimicrobial_audits")
    op.drop_index("ix_antimicrobial_audits_unit", table_name="antimicrobial_audits")
    op.drop_index("ix_antimicrobial_audits_cd_paciente", table_name="antimicrobial_audits")
    op.drop_index("ix_antimicrobial_audits_cd_atendimento", table_name="antimicrobial_audits")
    op.drop_index("ix_antimicrobial_audits_monitoring_run_id", table_name="antimicrobial_audits")
    op.drop_table("antimicrobial_audits")
