"""patient demographics and attendance metadata

Revision ID: 0024
Revises: 0023
Create Date: 2026-10-07 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pacientes", sa.Column("data_nascimento", sa.Date(), nullable=True))
    op.add_column("pacientes", sa.Column("sexo", sa.String(length=10), nullable=True))
    op.add_column("atendimentos", sa.Column("codigo_unidade", sa.String(length=60), nullable=True))
    op.add_column("atendimentos", sa.Column("codigo_leito", sa.String(length=60), nullable=True))
    op.add_column("atendimentos", sa.Column("codigo_prestador", sa.String(length=60), nullable=True))
    op.add_column("atendimentos", sa.Column("nome_prestador", sa.String(length=255), nullable=True))
    op.add_column("atendimentos", sa.Column("codigo_convenio", sa.String(length=60), nullable=True))
    op.add_column("atendimentos", sa.Column("nome_convenio", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("atendimentos", "nome_convenio")
    op.drop_column("atendimentos", "codigo_convenio")
    op.drop_column("atendimentos", "nome_prestador")
    op.drop_column("atendimentos", "codigo_prestador")
    op.drop_column("atendimentos", "codigo_leito")
    op.drop_column("atendimentos", "codigo_unidade")
    op.drop_column("pacientes", "sexo")
    op.drop_column("pacientes", "data_nascimento")
