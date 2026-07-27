"""allow hospital registration before token generation

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("hospital_integrations") as batch_op:
        batch_op.alter_column("token", existing_type=sa.String(length=120), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("hospital_integrations") as batch_op:
        batch_op.alter_column("token", existing_type=sa.String(length=120), nullable=False)
