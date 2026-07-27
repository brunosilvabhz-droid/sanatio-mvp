"""expand monitoring rule parameter value

Revision ID: 0002
Revises: 0001_initial
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("monitoring_rules") as batch_op:
        batch_op.alter_column("parameter_value", existing_type=sa.String(length=120), type_=sa.Text(), existing_nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("monitoring_rules") as batch_op:
        batch_op.alter_column("parameter_value", existing_type=sa.Text(), type_=sa.String(length=120), existing_nullable=False)
