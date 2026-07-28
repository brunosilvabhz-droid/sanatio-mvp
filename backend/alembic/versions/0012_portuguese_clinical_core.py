"""portuguese clinical core

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pacientes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_origem_paciente", sa.String(length=60), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id_origem_paciente"),
    )
    op.create_index(op.f("ix_pacientes_id_origem_paciente"), "pacientes", ["id_origem_paciente"], unique=True)

    op.create_table(
        "execucoes_integracao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hospital_integracao_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("total_pacientes_recebidos", sa.Integer(), nullable=False),
        sa.Column("total_snapshots_recebidos", sa.Integer(), nullable=False),
        sa.Column("total_movimentacoes_recebidas", sa.Integer(), nullable=False),
        sa.Column("total_alertas_gerados", sa.Integer(), nullable=False),
        sa.Column("mensagem_erro", sa.Text(), nullable=True),
        sa.Column("data_hora_inicio", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("data_hora_fim", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["hospital_integracao_id"], ["hospital_integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_execucoes_integracao_hospital_integracao_id"), "execucoes_integracao", ["hospital_integracao_id"], unique=False)
    op.create_index(op.f("ix_execucoes_integracao_status"), "execucoes_integracao", ["status"], unique=False)

    op.create_table(
        "atendimentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("paciente_id", sa.Integer(), nullable=False),
        sa.Column("id_origem_atendimento", sa.String(length=60), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("unidade_atual", sa.String(length=120), nullable=True),
        sa.Column("leito_atual", sa.String(length=120), nullable=True),
        sa.Column("data_hora_entrada", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_hora_saida", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id_origem_atendimento"),
    )
    op.create_index(op.f("ix_atendimentos_ativo"), "atendimentos", ["ativo"], unique=False)
    op.create_index(op.f("ix_atendimentos_id_origem_atendimento"), "atendimentos", ["id_origem_atendimento"], unique=True)
    op.create_index(op.f("ix_atendimentos_paciente_id"), "atendimentos", ["paciente_id"], unique=False)
    op.create_index(op.f("ix_atendimentos_unidade_atual"), "atendimentos", ["unidade_atual"], unique=False)

    op.create_table(
        "snapshots_atendimento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("atendimento_id", sa.Integer(), nullable=False),
        sa.Column("execucao_integracao_id", sa.Integer(), nullable=True),
        sa.Column("status_risco", sa.String(length=40), nullable=False),
        sa.Column("dias_internacao", sa.Integer(), nullable=False),
        sa.Column("possui_cultura_positiva", sa.Boolean(), nullable=False),
        sa.Column("maior_dias_antimicrobiano", sa.Integer(), nullable=False),
        sa.Column("maior_dias_dispositivo_invasivo", sa.Integer(), nullable=False),
        sa.Column("possui_isolamento_ativo", sa.Boolean(), nullable=False),
        sa.Column("data_hora_coleta", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["atendimento_id"], ["atendimentos.id"]),
        sa.ForeignKeyConstraint(["execucao_integracao_id"], ["execucoes_integracao.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("atendimento_id", "data_hora_coleta", name="uq_snapshot_atendimento_coleta"),
    )
    op.create_index(op.f("ix_snapshots_atendimento_atendimento_id"), "snapshots_atendimento", ["atendimento_id"], unique=False)
    op.create_index(op.f("ix_snapshots_atendimento_data_hora_coleta"), "snapshots_atendimento", ["data_hora_coleta"], unique=False)
    op.create_index(op.f("ix_snapshots_atendimento_execucao_integracao_id"), "snapshots_atendimento", ["execucao_integracao_id"], unique=False)
    op.create_index(op.f("ix_snapshots_atendimento_status_risco"), "snapshots_atendimento", ["status_risco"], unique=False)

    op.create_table(
        "movimentacoes_leito",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("atendimento_id", sa.Integer(), nullable=False),
        sa.Column("unidade_origem", sa.String(length=120), nullable=True),
        sa.Column("leito_origem", sa.String(length=120), nullable=True),
        sa.Column("unidade_destino", sa.String(length=120), nullable=True),
        sa.Column("leito_destino", sa.String(length=120), nullable=True),
        sa.Column("data_hora_movimentacao", sa.DateTime(timezone=True), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["atendimento_id"], ["atendimentos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("atendimento_id", "data_hora_movimentacao", "leito_destino", name="uq_movimentacao_leito_atendimento_hora_leito"),
    )
    op.create_index(op.f("ix_movimentacoes_leito_atendimento_id"), "movimentacoes_leito", ["atendimento_id"], unique=False)
    op.create_index(op.f("ix_movimentacoes_leito_data_hora_movimentacao"), "movimentacoes_leito", ["data_hora_movimentacao"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_movimentacoes_leito_data_hora_movimentacao"), table_name="movimentacoes_leito")
    op.drop_index(op.f("ix_movimentacoes_leito_atendimento_id"), table_name="movimentacoes_leito")
    op.drop_table("movimentacoes_leito")
    op.drop_index(op.f("ix_snapshots_atendimento_status_risco"), table_name="snapshots_atendimento")
    op.drop_index(op.f("ix_snapshots_atendimento_execucao_integracao_id"), table_name="snapshots_atendimento")
    op.drop_index(op.f("ix_snapshots_atendimento_data_hora_coleta"), table_name="snapshots_atendimento")
    op.drop_index(op.f("ix_snapshots_atendimento_atendimento_id"), table_name="snapshots_atendimento")
    op.drop_table("snapshots_atendimento")
    op.drop_index(op.f("ix_atendimentos_unidade_atual"), table_name="atendimentos")
    op.drop_index(op.f("ix_atendimentos_paciente_id"), table_name="atendimentos")
    op.drop_index(op.f("ix_atendimentos_id_origem_atendimento"), table_name="atendimentos")
    op.drop_index(op.f("ix_atendimentos_ativo"), table_name="atendimentos")
    op.drop_table("atendimentos")
    op.drop_index(op.f("ix_execucoes_integracao_status"), table_name="execucoes_integracao")
    op.drop_index(op.f("ix_execucoes_integracao_hospital_integracao_id"), table_name="execucoes_integracao")
    op.drop_table("execucoes_integracao")
    op.drop_index(op.f("ix_pacientes_id_origem_paciente"), table_name="pacientes")
    op.drop_table("pacientes")
