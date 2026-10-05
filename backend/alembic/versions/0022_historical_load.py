"""Historical integration load metadata.

Revision ID: 0022
Revises: 0021
"""

from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("execucoes_integracao", sa.Column("modo_carga", sa.String(40), nullable=False, server_default="INCREMENTAL"))
    op.add_column("execucoes_integracao", sa.Column("chave_lote", sa.String(160), nullable=True))
    op.add_column("execucoes_integracao", sa.Column("data_referencia", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_execucoes_integracao_modo_carga", "execucoes_integracao", ["modo_carga"])
    op.create_index("ix_execucoes_integracao_chave_lote", "execucoes_integracao", ["chave_lote"])
    op.create_index("ix_execucoes_integracao_data_referencia", "execucoes_integracao", ["data_referencia"])
    op.create_unique_constraint(
        "uq_execucao_integracao_hospital_lote",
        "execucoes_integracao",
        ["hospital_integracao_id", "chave_lote"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_execucao_integracao_hospital_lote", "execucoes_integracao", type_="unique")
    op.drop_index("ix_execucoes_integracao_data_referencia", table_name="execucoes_integracao")
    op.drop_index("ix_execucoes_integracao_chave_lote", table_name="execucoes_integracao")
    op.drop_index("ix_execucoes_integracao_modo_carga", table_name="execucoes_integracao")
    op.drop_column("execucoes_integracao", "data_referencia")
    op.drop_column("execucoes_integracao", "chave_lote")
    op.drop_column("execucoes_integracao", "modo_carga")
