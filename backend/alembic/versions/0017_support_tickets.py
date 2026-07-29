"""support tickets

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("requester_user_id", sa.Integer(), nullable=False),
        sa.Column("responder_user_id", sa.Integer(), nullable=True),
        sa.Column("admin_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["requester_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["responder_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_support_tickets_category"), "support_tickets", ["category"], unique=False)
    op.create_index(op.f("ix_support_tickets_requester_user_id"), "support_tickets", ["requester_user_id"], unique=False)
    op.create_index(op.f("ix_support_tickets_status"), "support_tickets", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_support_tickets_status"), table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_requester_user_id"), table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_category"), table_name="support_tickets")
    op.drop_table("support_tickets")
