"""epidemiology public references

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-11 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "referencias_epidemiologicas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo_indicador", sa.String(length=60), nullable=False),
        sa.Column("nome_indicador", sa.String(length=160), nullable=False),
        sa.Column("tipo_unidade", sa.String(length=120), nullable=False),
        sa.Column("populacao_referencia", sa.String(length=160), nullable=False),
        sa.Column("regiao", sa.String(length=80), nullable=True),
        sa.Column("uf", sa.String(length=2), nullable=True),
        sa.Column("ano_referencia", sa.Integer(), nullable=False),
        sa.Column("periodo_referencia", sa.String(length=40), nullable=True),
        sa.Column("p10", sa.Float(), nullable=True),
        sa.Column("p25", sa.Float(), nullable=True),
        sa.Column("p50", sa.Float(), nullable=True),
        sa.Column("p75", sa.Float(), nullable=True),
        sa.Column("p90", sa.Float(), nullable=True),
        sa.Column("unidade_medida", sa.String(length=80), nullable=False),
        sa.Column("fonte", sa.String(length=160), nullable=False),
        sa.Column("descricao_fonte", sa.Text(), nullable=True),
        sa.Column("url_fonte", sa.Text(), nullable=True),
        sa.Column("versao_referencia", sa.String(length=60), nullable=False),
        sa.Column("data_publicacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_importacao", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("data_criacao", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("data_atualizacao", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "codigo_indicador",
            "tipo_unidade",
            "populacao_referencia",
            "regiao",
            "uf",
            "ano_referencia",
            "periodo_referencia",
            "versao_referencia",
            name="uq_referencia_epidemiologica_versao",
        ),
    )
    for column in ["codigo_indicador", "nome_indicador", "tipo_unidade", "populacao_referencia", "regiao", "uf", "ano_referencia", "ativo"]:
        op.create_index(op.f(f"ix_referencias_epidemiologicas_{column}"), "referencias_epidemiologicas", [column], unique=False)

    op.create_table(
        "importacoes_referencias_epidemiologicas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome_arquivo", sa.String(length=255), nullable=False),
        sa.Column("fonte", sa.String(length=160), nullable=False),
        sa.Column("ano_referencia", sa.Integer(), nullable=True),
        sa.Column("quantidade_registros", sa.Integer(), server_default="0", nullable=False),
        sa.Column("quantidade_erros", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=40), server_default="EM_PROCESSAMENTO", nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("data_hora_inicio", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("data_hora_fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mensagem_erro", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_importacoes_referencias_epidemiologicas_ano_referencia"), "importacoes_referencias_epidemiologicas", ["ano_referencia"], unique=False)
    op.create_index(op.f("ix_importacoes_referencias_epidemiologicas_status"), "importacoes_referencias_epidemiologicas", ["status"], unique=False)
    op.create_index(op.f("ix_importacoes_referencias_epidemiologicas_usuario_id"), "importacoes_referencias_epidemiologicas", ["usuario_id"], unique=False)

    op.create_table(
        "perfis_estabelecimento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cnes", sa.String(length=20), nullable=False),
        sa.Column("nome_estabelecimento", sa.String(length=255), nullable=True),
        sa.Column("municipio", sa.String(length=120), nullable=True),
        sa.Column("uf", sa.String(length=2), nullable=True),
        sa.Column("quantidade_leitos", sa.Integer(), nullable=True),
        sa.Column("quantidade_leitos_uti", sa.Integer(), nullable=True),
        sa.Column("data_ultima_atualizacao_cnes", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fonte", sa.String(length=160), nullable=True),
        sa.Column("erro_ultima_atualizacao", sa.Text(), nullable=True),
        sa.Column("data_criacao", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("data_atualizacao", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnes"),
    )
    op.create_index(op.f("ix_perfis_estabelecimento_cnes"), "perfis_estabelecimento", ["cnes"], unique=False)

    op.create_table(
        "fechamentos_anvisa",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo_unidade", sa.String(length=120), server_default="UTI_ADULTO", nullable=False),
        sa.Column("periodo", sa.String(length=7), nullable=False),
        sa.Column("paciente_dia", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cvc_dia", sa.Integer(), server_default="0", nullable=False),
        sa.Column("vm_dia", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cvd_dia", sa.Integer(), server_default="0", nullable=False),
        sa.Column("casos_ipcsl", sa.Integer(), server_default="0", nullable=False),
        sa.Column("casos_pav", sa.Integer(), server_default="0", nullable=False),
        sa.Column("casos_itu_cvd", sa.Integer(), server_default="0", nullable=False),
        sa.Column("densidade_ipcsl", sa.Float(), server_default="0", nullable=False),
        sa.Column("densidade_pav", sa.Float(), server_default="0", nullable=False),
        sa.Column("densidade_itu_cvd", sa.Float(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=40), server_default="rascunho", nullable=False),
        sa.Column("validado_por", sa.Integer(), nullable=True),
        sa.Column("data_hora_validacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_criacao", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("data_atualizacao", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["validado_por"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tipo_unidade", "periodo", name="uq_fechamento_anvisa_tipo_periodo"),
    )
    op.create_index(op.f("ix_fechamentos_anvisa_periodo"), "fechamentos_anvisa", ["periodo"], unique=False)
    op.create_index(op.f("ix_fechamentos_anvisa_status"), "fechamentos_anvisa", ["status"], unique=False)
    op.create_index(op.f("ix_fechamentos_anvisa_tipo_unidade"), "fechamentos_anvisa", ["tipo_unidade"], unique=False)

    op.create_table(
        "logs_auditoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("data_hora", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("acao", sa.String(length=120), nullable=False),
        sa.Column("registro", sa.String(length=255), nullable=False),
        sa.Column("valor_anterior", sa.Text(), nullable=True),
        sa.Column("valor_novo", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_logs_auditoria_acao"), "logs_auditoria", ["acao"], unique=False)
    op.create_index(op.f("ix_logs_auditoria_usuario_id"), "logs_auditoria", ["usuario_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_logs_auditoria_usuario_id"), table_name="logs_auditoria")
    op.drop_index(op.f("ix_logs_auditoria_acao"), table_name="logs_auditoria")
    op.drop_table("logs_auditoria")
    op.drop_index(op.f("ix_fechamentos_anvisa_tipo_unidade"), table_name="fechamentos_anvisa")
    op.drop_index(op.f("ix_fechamentos_anvisa_status"), table_name="fechamentos_anvisa")
    op.drop_index(op.f("ix_fechamentos_anvisa_periodo"), table_name="fechamentos_anvisa")
    op.drop_table("fechamentos_anvisa")
    op.drop_index(op.f("ix_perfis_estabelecimento_cnes"), table_name="perfis_estabelecimento")
    op.drop_table("perfis_estabelecimento")
    op.drop_index(op.f("ix_importacoes_referencias_epidemiologicas_usuario_id"), table_name="importacoes_referencias_epidemiologicas")
    op.drop_index(op.f("ix_importacoes_referencias_epidemiologicas_status"), table_name="importacoes_referencias_epidemiologicas")
    op.drop_index(op.f("ix_importacoes_referencias_epidemiologicas_ano_referencia"), table_name="importacoes_referencias_epidemiologicas")
    op.drop_table("importacoes_referencias_epidemiologicas")
    for column in ["ativo", "ano_referencia", "uf", "regiao", "populacao_referencia", "tipo_unidade", "nome_indicador", "codigo_indicador"]:
        op.drop_index(op.f(f"ix_referencias_epidemiologicas_{column}"), table_name="referencias_epidemiologicas")
    op.drop_table("referencias_epidemiologicas")
