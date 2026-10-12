"""Contracts for the ephemeral authenticated Player v2 heartbeat."""

from datetime import datetime, timedelta, timezone as datetime_timezone
import hashlib
from uuid import uuid4

import pytest
from django.conf import settings
from django.db import transaction
from django.test import override_settings
from django.utils import timezone
from redis.exceptions import ConnectionError as RedisConnectionError

from nomenclatures.models import StationCredential
from nomenclatures.player_v2 import presence as station_presence
from nomenclatures.player_v2.playback.models import PlaybackEvent


def _headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Station {token}"}


def _credential(nomenclature, token: str) -> StationCredential:
    return StationCredential.objects.create(
        nomenclature=nomenclature,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )


def _presence_key(station_id) -> str:
    return f"station-presence:v1:{station_id}"


@override_settings(USE_TZ=True)
def test_presence_freshness_has_an_inclusive_ninety_second_boundary():
    now = datetime(2026, 10, 6, 5, 0, tzinfo=datetime_timezone.utc)
    station_id = uuid4()

    fresh = station_presence.get_station_presence(
        station_id,
        now=now,
        cached_value=(now - timedelta(seconds=90)).isoformat(),
    )
    stale = station_presence.get_station_presence(
        station_id,
        now=now,
        cached_value=(now - timedelta(seconds=91)).isoformat(),
    )

    assert fresh == {
        "status": "fresh",
        "last_seen": now - timedelta(seconds=90),
    }
    assert stale == {
        "status": "stale",
        "last_seen": now - timedelta(seconds=91),
    }


@pytest.mark.parametrize(
    "cached_value",
    (
        None,
        "not-a-datetime",
        {"last_seen": "2026-10-06T05:00:00+00:00"},
    ),
)
@override_settings(USE_TZ=True)
def test_absent_or_malformed_presence_is_unknown(cached_value):
    result = station_presence.get_station_presence(
        uuid4(),
        now=datetime(2026, 10, 6, 5, 0, tzinfo=datetime_timezone.utc),
        cached_value=cached_value,
    )

    assert result == {"status": "unknown", "last_seen": None}


@override_settings(USE_TZ=True)
def test_future_presence_is_unknown():
    now = datetime(2026, 10, 6, 5, 0, tzinfo=datetime_timezone.utc)

    result = station_presence.get_station_presence(
        uuid4(),
        now=now,
        cached_value=(now + timedelta(microseconds=1)).isoformat(),
    )

    assert result == {"status": "unknown", "last_seen": None}


@override_settings(USE_TZ=False)
def test_presence_uses_naive_datetimes_when_timezone_support_is_disabled():
    now = datetime(2026, 10, 6, 5, 0)

    result = station_presence.get_station_presence(
        uuid4(),
        now=now,
        cached_value=(now - timedelta(seconds=10)).isoformat(),
    )

    assert result == {
        "status": "fresh",
        "last_seen": now - timedelta(seconds=10),
    }


@override_settings(USE_TZ=True)
def test_naive_cached_timestamp_is_unknown_when_timezone_support_is_enabled():
    result = station_presence.get_station_presence(
        uuid4(),
        now=datetime(2026, 10, 6, 5, 0, tzinfo=datetime_timezone.utc),
        cached_value="2026-10-06T04:59:55",
    )

    assert result == {"status": "unknown", "last_seen": None}


@override_settings(USE_TZ=False)
def test_aware_cached_timestamp_is_unknown_when_timezone_support_is_disabled():
    result = station_presence.get_station_presence(
        uuid4(),
        now=datetime(2026, 10, 6, 5, 0),
        cached_value="2026-10-06T04:59:55+00:00",
    )

    assert result == {"status": "unknown", "last_seen": None}


@override_settings(USE_TZ=True)
def test_batch_presence_uses_one_cache_request(monkeypatch):
    now = datetime(2026, 10, 6, 5, 0, tzinfo=datetime_timezone.utc)
    fresh_id, stale_id, missing_id = uuid4(), uuid4(), uuid4()
    requested_keys = []

    def fake_get_many(keys):
        requested_keys.append(list(keys))
        return {
            _presence_key(fresh_id): (now - timedelta(seconds=5)).isoformat(),
            _presence_key(stale_id): (now - timedelta(minutes=5)).isoformat(),
        }

    monkeypatch.setattr(station_presence.cache, "get_many", fake_get_many)

    result = station_presence.load_station_presence(
        [fresh_id, stale_id, missing_id],
        now=now,
    )

    assert len(requested_keys) == 1
    assert set(requested_keys[0]) == {
        _presence_key(fresh_id),
        _presence_key(stale_id),
        _presence_key(missing_id),
    }
    assert result[str(fresh_id)]["status"] == "fresh"
    assert result[str(stale_id)]["status"] == "stale"
    assert result[str(missing_id)] == {"status": "unknown", "last_seen": None}


@override_settings(USE_TZ=True)
def test_batch_presence_treats_ignored_cache_failure_as_unknown(monkeypatch):
    station_ids = [uuid4(), uuid4()]
    monkeypatch.setattr(station_presence.cache, "get_many", lambda keys: None)

    result = station_presence.load_station_presence(
        station_ids,
        now=datetime(2026, 10, 6, 5, 0, tzinfo=datetime_timezone.utc),
    )

    assert result == {
        str(station_id): {"status": "unknown", "last_seen": None}
        for station_id in station_ids
    }


def test_single_presence_treats_cache_connection_failure_as_unknown(monkeypatch, caplog):
    def fail_cache_read(key):
        raise RedisConnectionError("redis unavailable")

    monkeypatch.setattr(station_presence.cache, "get", fail_cache_read)

    result = station_presence.get_station_presence(uuid4())

    assert result == {"status": "unknown", "last_seen": None}
    assert "cache is unavailable for a read (ConnectionError)" in caplog.text


def test_batch_presence_treats_cache_connection_failure_as_unknown(monkeypatch, caplog):
    station_id = uuid4()

    def fail_cache_read(keys):
        raise RedisConnectionError("redis unavailable")

    monkeypatch.setattr(station_presence.cache, "get_many", fail_cache_read)

    result = station_presence.load_station_presence([station_id])

    assert result == {
        str(station_id): {"status": "unknown", "last_seen": None},
    }
    assert "cache is unavailable for a batch read (ConnectionError)" in caplog.text


@pytest.mark.django_db
def test_successful_sync_records_presence_after_commit(
    client,
    nomenclature,
    django_capture_on_commit_callbacks,
    monkeypatch,
):
    token = "station-presence-success-token"
    _credential(nomenclature, token)
    writes = []
    monkeypatch.setattr(
        station_presence.cache,
        "set",
        lambda key, value, timeout: writes.append((key, value, timeout)),
    )

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            "/api/station/v2/sync/",
            data="{}",
            content_type="application/json",
            **_headers(token),
        )
        assert writes == []

    assert response.status_code == 200
    assert len(writes) == 1
    key, serialized_time, timeout = writes[0]
    assert key == _presence_key(nomenclature.pk)
    serialized_datetime = datetime.fromisoformat(serialized_time)
    assert timezone.is_aware(serialized_datetime) is settings.USE_TZ
    assert timeout == station_presence.PRESENCE_RETENTION_SECONDS


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("token", "payload", "expected_status"),
    (
        (None, "{}", 401),
        ("station-presence-invalid-token", '{"receipts":[{"command_id":"invalid"}]}', 400),
    ),
)
def test_rejected_sync_does_not_record_presence(
    client,
    nomenclature,
    django_capture_on_commit_callbacks,
    monkeypatch,
    token,
    payload,
    expected_status,
):
    if token is not None:
        _credential(nomenclature, token)
    writes = []
    monkeypatch.setattr(
        station_presence.cache,
        "set",
        lambda *args, **kwargs: writes.append((args, kwargs)),
    )
    headers = _headers(token) if token is not None else {}

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        response = client.post(
            "/api/station/v2/sync/",
            data=payload,
            content_type="application/json",
            **headers,
        )

    assert response.status_code == expected_status
    assert callbacks == []
    assert writes == []


@pytest.mark.django_db
def test_rolled_back_transaction_does_not_record_presence(
    django_capture_on_commit_callbacks,
    monkeypatch,
):
    writes = []
    monkeypatch.setattr(
        station_presence.cache,
        "set",
        lambda *args, **kwargs: writes.append((args, kwargs)),
    )

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        with pytest.raises(RuntimeError, match="force rollback"):
            with transaction.atomic():
                station_presence.schedule_station_presence(uuid4())
                raise RuntimeError("force rollback")

    assert callbacks == []
    assert writes == []


@pytest.mark.django_db
def test_cache_write_failure_does_not_fail_an_accepted_sync(
    client,
    nomenclature,
    django_capture_on_commit_callbacks,
    monkeypatch,
    caplog,
):
    token = "station-presence-cache-failure-token"
    _credential(nomenclature, token)

    def fail_cache_write(*args, **kwargs):
        raise RedisConnectionError("redis unavailable")

    monkeypatch.setattr(station_presence.cache, "set", fail_cache_write)

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            "/api/station/v2/sync/",
            data="{}",
            content_type="application/json",
            **_headers(token),
        )

    assert response.status_code == 200
    assert response.json()["commands"] == []
    assert "ConnectionError" in caplog.text
    assert token not in caplog.text


@pytest.mark.django_db
def test_cache_failure_keeps_the_durable_playback_ack(
    client, nomenclature, django_capture_on_commit_callbacks, monkeypatch
):
    token = "station-presence-playback-ack-token"
    _credential(nomenclature, token)
    event_id = str(uuid4())
    event = {
        "event_id": event_id,
        "station_id": str(nomenclature.pk),
        "playback_id": str(uuid4()),
        "event_sequence": 1,
        "event_type": "started",
        "occurred_at": "2026-10-06 09:00:00",
        "media_type": "video",
        "file_id": str(uuid4()),
        "order_id": None,
        "order_revision": None,
        "position_ms": 0,
        "duration_ms": 30000,
        "reason": None,
    }

    def fail_cache_write(*args, **kwargs):
        raise RedisConnectionError("redis unavailable")

    monkeypatch.setattr(station_presence.cache, "set", fail_cache_write)
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            "/api/station/v2/sync/",
            data={"playback_events": [event]},
            content_type="application/json",
            **_headers(token),
        )

    assert response.status_code == 200
    assert response.json()["playback_event_storage"] == "postgresql"
    assert response.json()["playback_events_stored"] == [event_id]
    assert PlaybackEvent.objects.filter(pk=event_id).exists()
