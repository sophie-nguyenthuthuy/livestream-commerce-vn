from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.stream import StreamEvent
from app.services.stream_service import _floor_minute


def test_floor_minute_strips_seconds() -> None:
    ts = datetime(2026, 5, 14, 14, 32, 47, 123456, tzinfo=UTC)
    out = _floor_minute(ts)
    assert out.second == 0 and out.microsecond == 0
    assert out.minute == 32


def test_floor_minute_converts_to_utc() -> None:
    from datetime import timedelta
    from datetime import timezone as tz
    ict = tz(timedelta(hours=7))
    ts = datetime(2026, 5, 14, 21, 5, 30, tzinfo=ict)
    out = _floor_minute(ts)
    assert out.tzinfo is not None
    assert out.utcoffset().total_seconds() == 0
    assert out.hour == 14


def test_stream_event_schema_rejects_negative_orders() -> None:
    import pydantic
    import pytest

    with pytest.raises(pydantic.ValidationError):
        StreamEvent(
            occurred_at=datetime.now(UTC),
            concurrent_viewers=100,
            orders=-1,
        )
