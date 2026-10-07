from datetime import date, datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from soulmv_integrator.sanatio_soulmv_integrator import (  # noqa: E402
    build_payload,
    connect,
    filter_historical_rows,
    query_specs,
    restrict_details_to_patients,
    split_payload,
)


def test_oracle_thick_mode_is_enabled_by_environment(monkeypatch) -> None:
    calls = []
    fake_connection = object()
    fake_oracledb = SimpleNamespace(
        init_oracle_client=lambda: calls.append("init"),
        clientversion=lambda: (19, 32, 0, 0, 0),
        connect=lambda dsn: calls.append(("connect", dsn)) or fake_connection,
    )
    monkeypatch.setitem(sys.modules, "oracledb", fake_oracledb)
    monkeypatch.setenv("SOULMV_ORACLE_THICK", "true")

    assert connect("oracle", "dsn-seguro") is fake_connection
    assert calls == ["init", ("connect", "dsn-seguro")]


def _rows():
    return {
        "patients": [
            {"cd_atendimento": "A1", "cd_paciente": "P1", "dt_atendimento": "2026-01-01", "dt_alta": None, "ds_unidade": "Atual"},
            {"cd_atendimento": "A2", "cd_paciente": "P2", "dt_atendimento": "2026-03-01", "dt_alta": None, "ds_unidade": "Fora"},
        ],
        "bed_movements": [
            {"cd_atendimento": "A1", "cd_paciente": "P1", "dt_movimentacao": "2026-01-10T10:00:00", "ds_unidade_destino": "UTI", "ds_leito_destino": "01"},
            {"cd_atendimento": "A2", "cd_paciente": "P2", "dt_movimentacao": "2026-03-02T10:00:00"},
        ],
        "antimicrobials": [],
        "cultures": [],
        "exam_requests": [],
        "invasive_procedures": [],
        "isolations": [],
    }


def test_historical_filter_state_and_batches() -> None:
    rows = filter_historical_rows(_rows(), date(2026, 1, 1), date(2026, 1, 31))
    assert [item["cd_atendimento"] for item in rows["patients"]] == ["A1"]
    assert [item["cd_atendimento"] for item in rows["bed_movements"]] == ["A1"]

    payload = build_payload(
        rows,
        {
            "antimicrobial_days_high": 7,
            "antimicrobial_days_medium": 4,
            "invasive_device_days_high": 7,
            "hospital_stay_days_high": 10,
            "hospital_stay_days_medium": 7,
        },
        date(2026, 1, 31),
    )
    assert payload["patients"][0]["unit"] == "UTI"
    assert payload["patients"][0]["bed"] == "01"
    assert payload["patients"][0]["days_in_hospital"] == 30

    batches = split_payload(
        payload,
        batch_size=1,
        batch_prefix="historica:2026-01-01:2026-01-31",
        reference_at=datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
    )
    assert len(batches) == 1
    assert batches[0]["modo_carga"] == "HISTORICA"
    assert batches[0]["chave_lote"].endswith("parte-0001-de-0001")


def test_incremental_queries_use_safe_date_parameters() -> None:
    views = {
        "patients": "SANATIO.VW_PACIENTES_ATENDIMENTOS",
        "bed_movements": "SANATIO.VW_MOVIMENTACOES_LEITO",
        "antimicrobials": "SANATIO.VW_ANTIMICROBIANOS",
        "cultures": "SANATIO.VW_CULTURAS",
        "exam_requests": "SANATIO.VW_SOLICITACOES_EXAMES",
        "invasive_procedures": "SANATIO.VW_PROCEDIMENTOS_INVASIVOS",
        "isolations": "SANATIO.VW_ISOLAMENTOS",
    }
    specs = {spec.key: spec for spec in query_specs(views, "oracle", 2)}

    assert "dt_alta IS NULL" in specs["patients"].sql
    assert "dt_fim IS NULL" in specs["antimicrobials"].sql
    assert "SYSDATE - :lookback_days" in specs["cultures"].sql
    assert specs["patients"].params == {"lookback_days": 2}


def test_optional_views_can_be_disabled() -> None:
    views = {
        "patients": "SANATIO.VW_SANATIO_PACIENTES_ATENDIMENTOS",
        "bed_movements": "SANATIO.VW_SANATIO_MOVIMENTACOES_LEITO",
        "antimicrobials": "SANATIO.VW_SANATIO_ANTIMICROBIANOS",
        "cultures": "",
        "exam_requests": "SANATIO.VW_SOLICITACOES_EXAMES",
        "invasive_procedures": "",
        "isolations": "",
    }

    specs = query_specs(views, "oracle", 2)

    assert {spec.key for spec in specs} == {
        "patients",
        "bed_movements",
        "antimicrobials",
        "exam_requests",
    }


def test_historical_queries_apply_period_in_database() -> None:
    views = {
        "patients": "SANATIO.VW_PACIENTES_ATENDIMENTOS",
        "bed_movements": "SANATIO.VW_MOVIMENTACOES_LEITO",
        "antimicrobials": "SANATIO.VW_ANTIMICROBIANOS",
        "cultures": "SANATIO.VW_CULTURAS",
        "exam_requests": "SANATIO.VW_SOLICITACOES_EXAMES",
        "invasive_procedures": "SANATIO.VW_PROCEDIMENTOS_INVASIVOS",
        "isolations": "SANATIO.VW_ISOLAMENTOS",
    }
    specs = query_specs(views, "postgres", 2, date(2025, 1, 1), date(2025, 1, 31))

    assert all("%(window_start)s" in spec.sql for spec in specs)
    assert all(spec.params["window_end"] == datetime(2025, 2, 1) for spec in specs)


def test_incremental_details_are_restricted_to_returned_attendances() -> None:
    rows = {
        "patients": [{"cd_atendimento": "10"}],
        "antimicrobials": [
            {"cd_atendimento": "10", "cd_prescricao": "1"},
            {"cd_atendimento": "99", "cd_prescricao": "2"},
        ],
        "isolations": [{"cd_atendimento": 10}, {"cd_atendimento": 20}],
    }

    restricted = restrict_details_to_patients(rows)

    assert restricted["patients"] == rows["patients"]
    assert [row["cd_prescricao"] for row in restricted["antimicrobials"]] == ["1"]
    assert len(restricted["isolations"]) == 1
