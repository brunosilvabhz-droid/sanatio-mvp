"""clinical detail tables

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "antimicrobianos_atendimento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("atendimento_id", sa.Integer(), nullable=False),
        sa.Column("id_origem_prescricao", sa.String(length=60), nullable=False),
        sa.Column("id_origem_item_prescricao", sa.String(length=60), nullable=False),
        sa.Column("id_origem_produto", sa.String(length=60), nullable=True),
        sa.Column("nome_antimicrobiano", sa.String(length=255), nullable=False),
        sa.Column("data_hora_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_hora_fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("dose", sa.String(length=120), nullable=True),
        sa.Column("via", sa.String(length=80), nullable=True),
        sa.Column("frequencia", sa.String(length=120), nullable=True),
        sa.Column("dias_uso", sa.Integer(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["atendimento_id"], ["atendimentos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("atendimento_id", "id_origem_prescricao", "id_origem_item_prescricao", name="uq_antimicrobiano_atendimento_prescricao_item"),
    )
    op.create_index(op.f("ix_antimicrobianos_atendimento_atendimento_id"), "antimicrobianos_atendimento", ["atendimento_id"])
    op.create_index(op.f("ix_antimicrobianos_atendimento_ativo"), "antimicrobianos_atendimento", ["ativo"])
    op.create_index(op.f("ix_antimicrobianos_atendimento_dias_uso"), "antimicrobianos_atendimento", ["dias_uso"])
    op.create_index(op.f("ix_antimicrobianos_atendimento_nome_antimicrobiano"), "antimicrobianos_atendimento", ["nome_antimicrobiano"])

    op.create_table(
        "culturas_atendimento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("atendimento_id", sa.Integer(), nullable=False),
        sa.Column("id_origem_pedido", sa.String(length=60), nullable=False),
        sa.Column("id_origem_exame", sa.String(length=60), nullable=False),
        sa.Column("exame", sa.String(length=255), nullable=False),
        sa.Column("material", sa.String(length=160), nullable=True),
        sa.Column("microorganismo", sa.String(length=255), nullable=True),
        sa.Column("resultado", sa.Text(), nullable=True),
        sa.Column("positivo", sa.Boolean(), nullable=False),
        sa.Column("data_hora_coleta", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_hora_resultado", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["atendimento_id"], ["atendimentos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("atendimento_id", "id_origem_pedido", "id_origem_exame", name="uq_cultura_atendimento_pedido_exame"),
    )
    op.create_index(op.f("ix_culturas_atendimento_atendimento_id"), "culturas_atendimento", ["atendimento_id"])
    op.create_index(op.f("ix_culturas_atendimento_data_hora_coleta"), "culturas_atendimento", ["data_hora_coleta"])
    op.create_index(op.f("ix_culturas_atendimento_positivo"), "culturas_atendimento", ["positivo"])

    op.create_table(
        "procedimentos_invasivos_atendimento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("atendimento_id", sa.Integer(), nullable=False),
        sa.Column("id_origem_procedimento", sa.String(length=60), nullable=False),
        sa.Column("procedimento", sa.String(length=255), nullable=False),
        sa.Column("local_instalacao", sa.String(length=160), nullable=True),
        sa.Column("data_hora_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_hora_fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("dias_permanencia", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["atendimento_id"], ["atendimentos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("atendimento_id", "id_origem_procedimento", "data_hora_inicio", name="uq_procedimento_invasivo_atendimento_origem_inicio"),
    )
    op.create_index(op.f("ix_procedimentos_invasivos_atendimento_atendimento_id"), "procedimentos_invasivos_atendimento", ["atendimento_id"])
    op.create_index(op.f("ix_procedimentos_invasivos_atendimento_ativo"), "procedimentos_invasivos_atendimento", ["ativo"])
    op.create_index(op.f("ix_procedimentos_invasivos_atendimento_dias_permanencia"), "procedimentos_invasivos_atendimento", ["dias_permanencia"])

    op.create_table(
        "isolamentos_atendimento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("atendimento_id", sa.Integer(), nullable=False),
        sa.Column("id_origem_isolamento", sa.String(length=60), nullable=False),
        sa.Column("isolamento", sa.String(length=255), nullable=False),
        sa.Column("data_hora_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_hora_fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["atendimento_id"], ["atendimentos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("atendimento_id", "id_origem_isolamento", "data_hora_inicio", name="uq_isolamento_atendimento_origem_inicio"),
    )
    op.create_index(op.f("ix_isolamentos_atendimento_atendimento_id"), "isolamentos_atendimento", ["atendimento_id"])
    op.create_index(op.f("ix_isolamentos_atendimento_ativo"), "isolamentos_atendimento", ["ativo"])


def downgrade() -> None:
    op.drop_index(op.f("ix_isolamentos_atendimento_ativo"), table_name="isolamentos_atendimento")
    op.drop_index(op.f("ix_isolamentos_atendimento_atendimento_id"), table_name="isolamentos_atendimento")
    op.drop_table("isolamentos_atendimento")
    op.drop_index(op.f("ix_procedimentos_invasivos_atendimento_dias_permanencia"), table_name="procedimentos_invasivos_atendimento")
    op.drop_index(op.f("ix_procedimentos_invasivos_atendimento_ativo"), table_name="procedimentos_invasivos_atendimento")
    op.drop_index(op.f("ix_procedimentos_invasivos_atendimento_atendimento_id"), table_name="procedimentos_invasivos_atendimento")
    op.drop_table("procedimentos_invasivos_atendimento")
    op.drop_index(op.f("ix_culturas_atendimento_positivo"), table_name="culturas_atendimento")
    op.drop_index(op.f("ix_culturas_atendimento_data_hora_coleta"), table_name="culturas_atendimento")
    op.drop_index(op.f("ix_culturas_atendimento_atendimento_id"), table_name="culturas_atendimento")
    op.drop_table("culturas_atendimento")
    op.drop_index(op.f("ix_antimicrobianos_atendimento_nome_antimicrobiano"), table_name="antimicrobianos_atendimento")
    op.drop_index(op.f("ix_antimicrobianos_atendimento_dias_uso"), table_name="antimicrobianos_atendimento")
    op.drop_index(op.f("ix_antimicrobianos_atendimento_ativo"), table_name="antimicrobianos_atendimento")
    op.drop_index(op.f("ix_antimicrobianos_atendimento_atendimento_id"), table_name="antimicrobianos_atendimento")
    op.drop_table("antimicrobianos_atendimento")
