"""Soul MV exam request identifiers for laboratory PDF matching.

Revision ID: 0021
Revises: 0020
"""

from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "solicitacoes_exames_atendimento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("atendimento_id", sa.Integer(), sa.ForeignKey("atendimentos.id"), nullable=False),
        sa.Column("id_origem_pedido", sa.String(60), nullable=False, unique=True),
        sa.Column("data_hora_solicitacao", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_solicitacoes_exames_atendimento_atendimento_id", "solicitacoes_exames_atendimento", ["atendimento_id"])
    op.create_index("ix_solicitacoes_exames_atendimento_id_origem_pedido", "solicitacoes_exames_atendimento", ["id_origem_pedido"])


def downgrade() -> None:
    op.drop_table("solicitacoes_exames_atendimento")
