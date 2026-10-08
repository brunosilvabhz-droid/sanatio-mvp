"""multi hospital users and staged laboratory imports

Revision ID: 0027
Revises: 0026
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_hospitals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospital_integrations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "hospital_id", name="uq_user_hospital"),
    )
    op.create_index("ix_user_hospitals_user_id", "user_hospitals", ["user_id"])
    op.create_index("ix_user_hospitals_hospital_id", "user_hospitals", ["hospital_id"])
    op.add_column("importacoes_pdf_laboratorio", sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospital_integrations.id"), nullable=True))
    op.add_column("importacoes_pdf_laboratorio", sa.Column("status", sa.String(length=20), server_default="VALIDADA", nullable=False))
    op.add_column("importacoes_pdf_laboratorio", sa.Column("validado_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column("importacoes_pdf_laboratorio", sa.Column("cancelado_em", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_importacoes_pdf_laboratorio_hospital_id", "importacoes_pdf_laboratorio", ["hospital_id"])
    op.create_index("ix_importacoes_pdf_laboratorio_status", "importacoes_pdf_laboratorio", ["status"])
    connection = op.get_bind()
    connection.execute(sa.text("INSERT INTO roles (name, description) SELECT 'SUPORTE_TI', 'Administracao de usuarios e suporte do hospital' WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name='SUPORTE_TI')"))
    connection.execute(sa.text("INSERT INTO user_hospitals (user_id, hospital_id) SELECT u.id, h.id FROM users u CROSS JOIN hospital_integrations h JOIN roles r ON r.id=u.role_id WHERE r.name <> 'ADMIN' ON CONFLICT DO NOTHING"))


def downgrade() -> None:
    op.drop_index("ix_importacoes_pdf_laboratorio_status", table_name="importacoes_pdf_laboratorio")
    op.drop_index("ix_importacoes_pdf_laboratorio_hospital_id", table_name="importacoes_pdf_laboratorio")
    op.drop_column("importacoes_pdf_laboratorio", "cancelado_em")
    op.drop_column("importacoes_pdf_laboratorio", "validado_em")
    op.drop_column("importacoes_pdf_laboratorio", "status")
    op.drop_column("importacoes_pdf_laboratorio", "hospital_id")
    op.drop_table("user_hospitals")
