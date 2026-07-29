"""remove legacy oracle settings

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-29 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEGACY_KEYS = (
    "oracle.connection.mode",
    "soulmv.view.patients",
    "soulmv.view.antimicrobials",
    "soulmv.view.cultures",
    "soulmv.view.invasive_procedures",
    "soulmv.view.isolations",
)


def upgrade() -> None:
    quoted = ", ".join(f"'{key}'" for key in LEGACY_KEYS)
    op.execute(f"DELETE FROM settings WHERE key IN ({quoted})")


def downgrade() -> None:
    pass
