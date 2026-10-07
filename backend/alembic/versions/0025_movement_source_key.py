"""movement source key

Revision ID: 0025
Revises: 0024
Create Date: 2026-10-07 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_movimentacao_leito_atendimento_hora_leito", "movimentacoes_leito", type_="unique")
    op.add_column("movimentacoes_leito", sa.Column("chave_origem", sa.String(length=64), nullable=True))
    op.create_index("ix_movimentacoes_leito_chave_origem", "movimentacoes_leito", ["chave_origem"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_movimentacoes_leito_chave_origem", table_name="movimentacoes_leito")
    op.drop_column("movimentacoes_leito", "chave_origem")
    op.create_unique_constraint(
        "uq_movimentacao_leito_atendimento_hora_leito",
        "movimentacoes_leito",
        ["atendimento_id", "data_hora_movimentacao", "leito_destino"],
    )
