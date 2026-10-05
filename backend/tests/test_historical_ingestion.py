from datetime import datetime, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all tables in Base metadata
from app.api.routes.ingestion import ingest_snapshots
from app.models.alert import Alert
from app.models.antimicrobial_audit import AntimicrobialAudit
from app.models.base import Base
from app.models.clinical import ExecucaoIntegracao, SnapshotAtendimento
from app.models.hospital_integration import HospitalIntegration
from app.models.patient_monitoring_snapshot import PatientMonitoringSnapshot
from app.schemas.hospital_integration import IngestPayload


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def _payload() -> IngestPayload:
    return IngestPayload.model_validate(
        {
            "modo_carga": "HISTORICA",
            "data_referencia": "2026-01-31T23:59:59+00:00",
            "chave_lote": "historica:2026-01-01:2026-01-31:parte-0001-de-0001",
            "patients": [
                {
                    "cd_atendimento": "AT-1",
                    "cd_paciente": "PAC-1",
                    "unit": "UTI Adulto",
                    "bed": "UTI-01",
                    "active": True,
                    "admitted_at": "2026-01-01T10:00:00+00:00",
                }
            ],
            "antimicrobials": [
                {
                    "cd_atendimento": "AT-1",
                    "cd_paciente": "PAC-1",
                    "cd_prescricao": "P-1",
                    "cd_item_prescricao": "I-1",
                    "ds_antimicrobiano": "Medicamento de teste",
                    "ds_principio_ativo": "Principio ativo de teste",
                    "dt_inicio": "2026-01-02T08:00:00+00:00",
                    "dt_aplicacao": "2026-01-02T09:00:00+00:00",
                    "sn_ativo": "S",
                }
            ],
            "cultures": [
                {
                    "cd_atendimento": "AT-1",
                    "cd_paciente": "PAC-1",
                    "cd_pedido": "PED-1",
                    "cd_exame": "EX-1",
                    "ds_exame": "Hemocultura",
                    "dt_coleta": "2026-01-10T10:00:00+00:00",
                    "sn_positivo": "S",
                }
            ],
        }
    )


def test_historical_load_is_silent_and_idempotent() -> None:
    db = _session()
    integration = HospitalIntegration(hospital_name="Hospital Teste", token="token-historico", active=True)
    db.add(integration)
    db.commit()

    first = ingest_snapshots(_payload(), "token-historico", db)

    assert first["modo_carga"] == "HISTORICA"
    assert first["duplicate"] is False
    assert first["alerts_created"] == 0
    assert db.scalar(select(func.count(Alert.id))) == 0
    assert db.scalar(select(func.count(AntimicrobialAudit.id))) == 0

    clinical_snapshot = db.scalar(select(SnapshotAtendimento))
    operational_snapshot = db.scalar(select(PatientMonitoringSnapshot))
    run = db.scalar(select(ExecucaoIntegracao))
    assert clinical_snapshot is not None
    assert clinical_snapshot.dias_internacao == 30
    assert clinical_snapshot.maior_dias_antimicrobiano == 29
    assert clinical_snapshot.possui_cultura_positiva is True
    assert operational_snapshot is not None
    assert operational_snapshot.collected_at.replace(tzinfo=timezone.utc) == datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
    assert run is not None
    assert run.chave_lote == _payload().chave_lote

    second = ingest_snapshots(_payload(), "token-historico", db)

    assert second["duplicate"] is True
    assert db.scalar(select(func.count(ExecucaoIntegracao.id))) == 1
    assert db.scalar(select(func.count(SnapshotAtendimento.id))) == 1
    assert db.scalar(select(func.count(PatientMonitoringSnapshot.id))) == 1
    db.close()
