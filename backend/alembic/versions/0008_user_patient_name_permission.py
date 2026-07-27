"""user patient name permission

Revision ID: 0008
Revises: 0007_antimicrobial_audits
Create Date: 2026-07-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("can_view_patient_name", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute(
        """
        UPDATE users
        SET can_view_patient_name = TRUE
        WHERE role_id IN (SELECT id FROM roles WHERE name IN ('ADMIN', 'SCIH'))
        """
    )
    op.execute(
        """
        INSERT INTO roles (name, description)
        SELECT 'MEDICO', 'Medico assistente'
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'MEDICO')
        """
    )
    op.execute(
        """
        INSERT INTO roles (name, description)
        SELECT 'INFECTO', 'Infectologista'
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'INFECTO')
        """
    )


def downgrade() -> None:
    op.drop_column("users", "can_view_patient_name")
    op.execute("DELETE FROM roles WHERE name IN ('MEDICO', 'INFECTO')")
