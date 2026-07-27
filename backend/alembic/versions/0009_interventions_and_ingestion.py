"""interventions and hospital ingestion

Revision ID: 0009_interventions_and_ingestion
Revises: 0008_user_patient_name_permission
Create Date: 2026-07-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_interventions_and_ingestion"
down_revision: str | None = "0008_user_patient_name_permission"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hospital_integrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hospital_name", sa.String(length=255), nullable=False),
        sa.Column("token", sa.String(length=120), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_hospital_integrations_token"), "hospital_integrations", ["token"], unique=False)

    op.create_table(
        "intervention_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cd_atendimento", sa.String(length=60), nullable=False),
        sa.Column("cd_paciente", sa.String(length=60), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="ENVIADA", nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("responded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("response", sa.String(length=40), nullable=True),
        sa.Column("response_justification", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["responded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_intervention_requests_cd_atendimento"), "intervention_requests", ["cd_atendimento"], unique=False)
    op.create_index(op.f("ix_intervention_requests_cd_paciente"), "intervention_requests", ["cd_paciente"], unique=False)
    op.create_index(op.f("ix_intervention_requests_source_id"), "intervention_requests", ["source_id"], unique=False)
    op.create_index(op.f("ix_intervention_requests_status"), "intervention_requests", ["status"], unique=False)

    op.create_table(
        "intervention_recipients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("intervention_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="ENVIADO", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["intervention_id"], ["intervention_requests.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "patient_timeline_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cd_atendimento", sa.String(length=60), nullable=False),
        sa.Column("cd_paciente", sa.String(length=60), nullable=False),
        sa.Column("note_type", sa.String(length=40), server_default="EVOLUCAO", nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patient_timeline_notes_cd_atendimento"), "patient_timeline_notes", ["cd_atendimento"], unique=False)
    op.create_index(op.f("ix_patient_timeline_notes_cd_paciente"), "patient_timeline_notes", ["cd_paciente"], unique=False)

    settings = sa.table(
        "settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
        sa.column("description", sa.String),
    )
    connection = op.get_bind()
    for key, value, description in [
        ("alerts.threshold.antimicrobial_days", "7", "Dias de antimicrobiano ativo para gerar alerta"),
        ("alerts.threshold.invasive_device_days", "7", "Dias de procedimento invasivo ativo para gerar alerta"),
        ("alerts.threshold.hospital_stay_days", "10", "Dias de internacao para gerar alerta"),
    ]:
        exists = connection.execute(sa.select(sa.literal(1)).select_from(settings).where(settings.c.key == key)).first()
        if not exists:
            connection.execute(settings.insert().values(key=key, value=value, description=description))


def downgrade() -> None:
    op.drop_index(op.f("ix_patient_timeline_notes_cd_paciente"), table_name="patient_timeline_notes")
    op.drop_index(op.f("ix_patient_timeline_notes_cd_atendimento"), table_name="patient_timeline_notes")
    op.drop_table("patient_timeline_notes")
    op.drop_table("intervention_recipients")
    op.drop_index(op.f("ix_intervention_requests_status"), table_name="intervention_requests")
    op.drop_index(op.f("ix_intervention_requests_source_id"), table_name="intervention_requests")
    op.drop_index(op.f("ix_intervention_requests_cd_paciente"), table_name="intervention_requests")
    op.drop_index(op.f("ix_intervention_requests_cd_atendimento"), table_name="intervention_requests")
    op.drop_table("intervention_requests")
    op.drop_index(op.f("ix_hospital_integrations_token"), table_name="hospital_integrations")
    op.drop_table("hospital_integrations")
