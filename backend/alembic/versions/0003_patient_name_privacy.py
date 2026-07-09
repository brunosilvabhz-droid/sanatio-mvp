"""patient name privacy

Revision ID: 0003_patient_name_privacy
Revises: 0002_expand_monitoring_rule_parameter
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_patient_name_privacy"
down_revision = "0002_expand_monitoring_rule_parameter"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.alter_column("patient_name", existing_type=sa.String(length=255), nullable=True)
    op.execute("UPDATE alerts SET patient_name = NULL")


def downgrade() -> None:
    op.execute("UPDATE alerts SET patient_name = COALESCE(patient_name, 'Paciente não identificado')")
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.alter_column("patient_name", existing_type=sa.String(length=255), nullable=False)
