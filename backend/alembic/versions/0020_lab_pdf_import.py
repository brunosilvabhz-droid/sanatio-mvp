"""Laboratory PDF import staging and reviewed patient links.

Revision ID: 0020
Revises: 0019
"""

from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "importacoes_pdf_laboratorio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome_arquivo", sa.String(255), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("paginas", sa.Integer(), nullable=False),
        sa.Column("total_resultados", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("importado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "resultados_pdf_laboratorio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("importacao_id", sa.Integer(), sa.ForeignKey("importacoes_pdf_laboratorio.id"), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("pagina", sa.Integer(), nullable=False),
        sa.Column("os_pedido", sa.String(60), nullable=False),
        sa.Column("nome_relatorio", sa.String(255)),
        sa.Column("data_coleta", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_resultado", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exame_amostra", sa.Text(), nullable=False),
        sa.Column("resultado", sa.Text(), nullable=False),
        sa.Column("situacao", sa.String(20), nullable=False),
        sa.Column("atendimento_sugerido_id", sa.Integer(), sa.ForeignKey("atendimentos.id")),
        sa.Column("atendimento_id", sa.Integer(), sa.ForeignKey("atendimentos.id")),
        sa.Column("vinculado_por_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("vinculado_em", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("importacao_id", "ordem", name="uq_resultado_pdf_importacao_ordem"),
    )
    op.create_index("ix_resultados_pdf_laboratorio_importacao_id", "resultados_pdf_laboratorio", ["importacao_id"])
    op.create_index("ix_resultados_pdf_laboratorio_os_pedido", "resultados_pdf_laboratorio", ["os_pedido"])
    op.create_index("ix_resultados_pdf_laboratorio_atendimento_id", "resultados_pdf_laboratorio", ["atendimento_id"])


def downgrade() -> None:
    op.drop_table("resultados_pdf_laboratorio")
    op.drop_table("importacoes_pdf_laboratorio")
