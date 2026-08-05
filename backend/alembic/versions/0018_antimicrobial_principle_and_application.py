"""antimicrobial principle and application date

Revision ID: 0018
Revises: 0017
Create Date: 2026-08-03 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("antimicrobianos_atendimento", sa.Column("principio_ativo", sa.String(length=255), nullable=True))
    op.add_column("antimicrobianos_atendimento", sa.Column("data_hora_aplicacao", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE antimicrobianos_atendimento SET principio_ativo = nome_antimicrobiano WHERE principio_ativo IS NULL")
    op.execute("UPDATE antimicrobianos_atendimento SET data_hora_aplicacao = data_hora_inicio WHERE data_hora_aplicacao IS NULL")
    op.create_index(op.f("ix_antimicrobianos_atendimento_principio_ativo"), "antimicrobianos_atendimento", ["principio_ativo"], unique=False)
    op.create_index(op.f("ix_antimicrobianos_atendimento_data_hora_aplicacao"), "antimicrobianos_atendimento", ["data_hora_aplicacao"], unique=False)
    with op.batch_alter_table("antimicrobianos_atendimento") as batch_op:
        batch_op.drop_constraint("uq_antimicrobiano_atendimento_prescricao_item", type_="unique")
        batch_op.create_unique_constraint(
            "uq_antimicrobiano_atendimento_prescricao_item_aplicacao",
            ["atendimento_id", "id_origem_prescricao", "id_origem_item_prescricao", "data_hora_aplicacao"],
        )


def downgrade() -> None:
    with op.batch_alter_table("antimicrobianos_atendimento") as batch_op:
        batch_op.drop_constraint("uq_antimicrobiano_atendimento_prescricao_item_aplicacao", type_="unique")
        batch_op.create_unique_constraint(
            "uq_antimicrobiano_atendimento_prescricao_item",
            ["atendimento_id", "id_origem_prescricao", "id_origem_item_prescricao"],
        )
    op.drop_index(op.f("ix_antimicrobianos_atendimento_data_hora_aplicacao"), table_name="antimicrobianos_atendimento")
    op.drop_index(op.f("ix_antimicrobianos_atendimento_principio_ativo"), table_name="antimicrobianos_atendimento")
    op.drop_column("antimicrobianos_atendimento", "data_hora_aplicacao")
    op.drop_column("antimicrobianos_atendimento", "principio_ativo")
