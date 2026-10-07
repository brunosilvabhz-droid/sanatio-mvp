from datetime import datetime, timezone

from app.services.antimicrobial_audit_service import treatment_courses


def prescription(code: str, start: str, end: str | None, active: str = "S") -> dict:
    return {
        "cd_prescricao": code,
        "cd_item_prescricao": "1",
        "ds_antimicrobiano": "Meropenem",
        "ds_principio_ativo": "MEROPENEM",
        "dt_inicio": datetime.fromisoformat(start).replace(tzinfo=timezone.utc),
        "dt_aplicacao": datetime.fromisoformat(start).replace(tzinfo=timezone.utc),
        "dt_fim": datetime.fromisoformat(end).replace(tzinfo=timezone.utc) if end else None,
        "sn_ativo": active,
    }


def test_finished_prescription_continues_in_later_prescription_of_same_medication():
    courses, _ = treatment_courses(
        [
            prescription("10", "2026-10-01T08:00:00", "2026-10-05T08:00:00", "N"),
            prescription("11", "2026-10-05T09:00:00", None, "S"),
        ],
        now=datetime(2026, 10, 10, tzinfo=timezone.utc),
    )

    assert len(courses) == 1
    assert courses[0]["cd_prescricao"] == "11"
    assert courses[0]["sn_ativo"] == "S"
    assert courses[0]["dias_uso"] == 9


def test_end_date_does_not_close_latest_prescription_when_flag_is_active():
    courses, _ = treatment_courses(
        [prescription("10", "2026-10-01T08:00:00", "2026-10-05T08:00:00", "S")],
        now=datetime(2026, 10, 10, tzinfo=timezone.utc),
    )

    assert courses[0]["sn_ativo"] == "S"
    assert courses[0]["dias_uso"] == 9


def test_gap_longer_than_one_day_starts_new_course():
    courses, _ = treatment_courses(
        [
            prescription("10", "2026-10-01T08:00:00", "2026-10-03T08:00:00", "N"),
            prescription("11", "2026-10-06T08:00:00", None, "S"),
        ],
        now=datetime(2026, 10, 10, tzinfo=timezone.utc),
    )

    assert len(courses) == 2
    assert courses[-1]["dias_uso"] == 4
