from datetime import date, datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from soulmv_integrator.sanatio_soulmv_integrator import (  # noqa: E402
    build_payload,
    filter_historical_rows,
    split_payload,
)


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
