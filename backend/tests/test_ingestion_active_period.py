from datetime import datetime, timezone

from app.api.routes.ingestion import _active_until


NOW = datetime(2026, 10, 8, 12, tzinfo=timezone.utc)


def test_active_record_with_future_end_date_remains_active() -> None:
    assert _active_until("S", datetime(2026, 10, 9, 12, tzinfo=timezone.utc), NOW)


def test_active_record_with_expired_end_date_is_closed() -> None:
    assert not _active_until("S", datetime(2026, 10, 8, 11, tzinfo=timezone.utc), NOW)


def test_cancelled_record_stays_closed_even_with_future_end_date() -> None:
    assert not _active_until("N", datetime(2026, 10, 9, 12, tzinfo=timezone.utc), NOW)
