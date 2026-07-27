"""internal rule fields

Revision ID: 0006
Revises: 0005_patient_monitoring_snapshots
Create Date: 2026-07-10
"""
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE monitoring_rules
        SET rule_type = 'ANTIMICROBIAL_DAYS',
            parameter_key = 'max_antimicrobial_days'
        WHERE rule_type = 'ANTIMICROBIAL_GT7'
        """
    )
    op.execute(
        """
        UPDATE monitoring_rules
        SET rule_type = 'INVASIVE_DEVICE_DAYS',
            parameter_key = 'max_invasive_device_days'
        WHERE rule_type = 'INVASIVE_GT7'
        """
    )
    op.execute("UPDATE monitoring_rules SET parameter_key = 'has_positive_culture', parameter_value = 'true' WHERE rule_type = 'POSITIVE_CULTURE'")
    op.execute("UPDATE monitoring_rules SET parameter_key = 'days_in_hospital' WHERE rule_type = 'LONG_STAY'")
    op.execute("UPDATE monitoring_rules SET parameter_key = 'has_active_isolation', parameter_value = 'true' WHERE rule_type = 'ACTIVE_ISOLATION'")


def downgrade() -> None:
    op.execute(
        """
        UPDATE monitoring_rules
        SET rule_type = 'ANTIMICROBIAL_GT7',
            parameter_key = 'dias_uso'
        WHERE rule_type = 'ANTIMICROBIAL_DAYS'
        """
    )
    op.execute(
        """
        UPDATE monitoring_rules
        SET rule_type = 'INVASIVE_GT7',
            parameter_key = 'dias_permanencia'
        WHERE rule_type = 'INVASIVE_DEVICE_DAYS'
        """
    )
    op.execute("UPDATE monitoring_rules SET parameter_key = 'sn_positivo', parameter_value = 'S' WHERE rule_type = 'POSITIVE_CULTURE'")
    op.execute("UPDATE monitoring_rules SET parameter_key = 'dias_internacao' WHERE rule_type = 'LONG_STAY'")
    op.execute("UPDATE monitoring_rules SET parameter_key = 'sn_ativo', parameter_value = 'S' WHERE rule_type = 'ACTIVE_ISOLATION'")
