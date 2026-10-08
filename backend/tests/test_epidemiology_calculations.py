from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.models.base import Base
from app.models.clinical import Atendimento, Paciente
from app.services.benchmark_epidemiologico_service import BenchmarkEpidemiologicoService
from app.api.routes.epidemiology import _numeric_quantity


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_patient_days_respects_adult_icu_and_cti_alias() -> None:
    db = _session()
    patient = Paciente(id_origem_paciente="P1")
    db.add(patient)
    db.flush()
    db.add_all(
        [
            Atendimento(
                paciente_id=patient.id,
                id_origem_atendimento="A1",
                unidade_atual="CTI",
                data_hora_entrada=datetime(2026, 10, 1, tzinfo=timezone.utc),
                data_hora_saida=datetime(2026, 10, 4, tzinfo=timezone.utc),
                ativo=False,
            ),
            Atendimento(
                paciente_id=patient.id,
                id_origem_atendimento="A2",
                unidade_atual="UI 7 ANDAR",
                data_hora_entrada=datetime(2026, 10, 1, tzinfo=timezone.utc),
                data_hora_saida=datetime(2026, 10, 10, tzinfo=timezone.utc),
                ativo=False,
            ),
        ]
    )
    db.commit()

    total = BenchmarkEpidemiologicoService(db).patient_days(
        datetime(2026, 10, 1, tzinfo=timezone.utc),
        datetime(2026, 11, 1, tzinfo=timezone.utc),
        "UTI_ADULTO",
    )

    assert total == 3
    db.close()


def test_ml_quantity_is_parsed_without_affecting_dot_units() -> None:
    assert _numeric_quantity("150") == 150.0
    assert _numeric_quantity("5,5") == 5.5
    assert _numeric_quantity(None) == 0.0
