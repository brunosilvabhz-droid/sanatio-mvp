"""antimicrobial product catalog and administered quantity

Revision ID: 0026
Revises: 0025
Create Date: 2026-10-07 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "produtos_antimicrobianos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo_produto", sa.String(length=60), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=False),
        sa.Column("quantidade", sa.String(length=80), nullable=False),
        sa.Column("unidade_medida", sa.String(length=20), nullable=False),
        sa.Column("codigo_atc", sa.String(length=20), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("codigo_produto"),
    )
    op.create_index("ix_produtos_antimicrobianos_codigo_produto", "produtos_antimicrobianos", ["codigo_produto"], unique=True)
    op.create_index("ix_produtos_antimicrobianos_codigo_atc", "produtos_antimicrobianos", ["codigo_atc"])
    op.add_column("antimicrobianos_atendimento", sa.Column("quantidade_dose", sa.Numeric(18, 4), nullable=True))
    op.add_column("antimicrobianos_atendimento", sa.Column("quantidade_total", sa.String(length=120), nullable=True))
    op.add_column("antimicrobianos_atendimento", sa.Column("quantidade_total_gramas", sa.Numeric(18, 6), nullable=True))
    op.add_column("antimicrobianos_atendimento", sa.Column("unidade_quantidade_total", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("antimicrobianos_atendimento", "unidade_quantidade_total")
    op.drop_column("antimicrobianos_atendimento", "quantidade_total_gramas")
    op.drop_column("antimicrobianos_atendimento", "quantidade_total")
    op.drop_column("antimicrobianos_atendimento", "quantidade_dose")
    op.drop_index("ix_produtos_antimicrobianos_codigo_atc", table_name="produtos_antimicrobianos")
    op.drop_index("ix_produtos_antimicrobianos_codigo_produto", table_name="produtos_antimicrobianos")
    op.drop_table("produtos_antimicrobianos")
