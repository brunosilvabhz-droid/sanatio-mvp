"""antimicrobial alert subtypes

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-29 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    settings = [
        ("alerts.threshold.same_antimicrobial_days", "7", "Dias de uso continuo do mesmo antimicrobiano/principio ativo para gerar alerta"),
        ("alerts.threshold.antimicrobial_exposure_days", "14", "Dias consecutivos com algum antimicrobiano para gerar alerta"),
        ("alerts.threshold.antimicrobial_scheme_changes_count", "3", "Quantidade de alteracoes de esquema antimicrobiano para gerar alerta"),
        ("alerts.threshold.antimicrobial_scheme_changes_window_days", "7", "Janela em dias para avaliar trocas frequentes de esquema"),
    ]
    for key, value, description in settings:
        op.execute(
            f"""
            INSERT INTO settings (key, value, description)
            SELECT '{key}', '{value}', '{description}'
            WHERE NOT EXISTS (SELECT 1 FROM settings WHERE key = '{key}')
            """
        )

    rules = [
        ("Mesmo antimicrobiano prolongado", "ANTIMICROBIAL_SAME_PROLONGED", "same_antimicrobial_days", "7", "MEDIA"),
        ("Exposicao antimicrobiana prolongada", "ANTIMICROBIAL_EXPOSURE_PROLONGED", "antimicrobial_exposure_days", "14", "ALTA"),
        ("Trocas frequentes de esquema antimicrobiano", "ANTIMICROBIAL_FREQUENT_SCHEME_CHANGES", "scheme_changes_in_window", "3/7", "ALTA"),
    ]
    for name, rule_type, parameter_key, parameter_value, severity in rules:
        op.execute(
            f"""
            INSERT INTO monitoring_rules (name, description, rule_type, parameter_key, parameter_value, severity, active)
            SELECT '{name}', '{name}', '{rule_type}', '{parameter_key}', '{parameter_value}', '{severity}', true
            WHERE NOT EXISTS (SELECT 1 FROM monitoring_rules WHERE rule_type = '{rule_type}')
            """
        )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM monitoring_rules
        WHERE rule_type IN (
            'ANTIMICROBIAL_SAME_PROLONGED',
            'ANTIMICROBIAL_EXPOSURE_PROLONGED',
            'ANTIMICROBIAL_FREQUENT_SCHEME_CHANGES'
        )
        """
    )
    op.execute(
        """
        DELETE FROM settings
        WHERE key IN (
            'alerts.threshold.same_antimicrobial_days',
            'alerts.threshold.antimicrobial_exposure_days',
            'alerts.threshold.antimicrobial_scheme_changes_count',
            'alerts.threshold.antimicrobial_scheme_changes_window_days'
        )
        """
    )
