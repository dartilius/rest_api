"""Ephemeral connection freshness for authenticated Player v2 stations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta
import logging
from typing import Literal, TypedDict
from uuid import UUID

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django_redis.exceptions import ConnectionInterrupted
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)

FRESH_FOR = timedelta(seconds=90)
PRESENCE_RETENTION_SECONDS = 7 * 24 * 60 * 60
_CACHE_KEY_PREFIX = "station-presence:v1"
_NOT_PROVIDED = object()
_CACHE_ERRORS = (ConnectionInterrupted, RedisError, ConnectionError, TimeoutError)


class StationPresence(TypedDict):
    status: Literal["fresh", "stale", "unknown"]
    last_seen: datetime | None


def _cache_key(station_id: UUID | str) -> str:
    return f"{_CACHE_KEY_PREFIX}:{station_id}"


def _unknown_presence() -> StationPresence:
    return {"status": "unknown", "last_seen": None}


def _coerce_for_current_timezone(value: datetime) -> datetime | None:
    """Return a datetime compatible with the project's current USE_TZ mode."""
    if settings.USE_TZ:
        if timezone.is_naive(value):
            return None
        return value
    if timezone.is_aware(value):
        return None
    return value


def _deserialize_last_seen(value: object) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
    else:
        return None
    return _coerce_for_current_timezone(parsed)


def _read_presence_value(station_id: UUID | str) -> object:
    try:
        return cache.get(_cache_key(station_id))
    except _CACHE_ERRORS as exc:
        logger.warning(
            "Player v2 station presence cache is unavailable for a read (%s).",
            type(exc).__name__,
        )
        return None


def get_station_presence(
    station_id: UUID | str,
    *,
    now: datetime | None = None,
    cached_value: object = _NOT_PROVIDED,
) -> StationPresence:
    """Classify one station heartbeat without implying playback health."""
    current_time = _coerce_for_current_timezone(now or timezone.now())
    if current_time is None:
        return _unknown_presence()

    if cached_value is _NOT_PROVIDED:
        cached_value = _read_presence_value(station_id)
    last_seen = _deserialize_last_seen(cached_value)
    if last_seen is None:
        return _unknown_presence()

    age = current_time - last_seen
    if age < timedelta(0):
        return _unknown_presence()
    return {
        "status": "fresh" if age <= FRESH_FOR else "stale",
        "last_seen": last_seen,
    }


def load_station_presence(
    station_ids: Iterable[UUID | str],
    *,
    now: datetime | None = None,
) -> dict[str, StationPresence]:
    """Load a page of station heartbeats with one cache request."""
    station_keys = {str(station_id): _cache_key(station_id) for station_id in station_ids}
    if not station_keys:
        return {}

    try:
        cached_values = cache.get_many(station_keys.values())
    except _CACHE_ERRORS as exc:
        logger.warning(
            "Player v2 station presence cache is unavailable for a batch read (%s).",
            type(exc).__name__,
        )
        cached_values = {}
    if not isinstance(cached_values, Mapping):
        cached_values = {}

    current_time = now or timezone.now()
    return {
        station_id: get_station_presence(
            station_id,
            now=current_time,
            cached_value=cached_values.get(cache_key),
        )
        for station_id, cache_key in station_keys.items()
    }


def schedule_station_presence(
    station_id: UUID | str,
    *,
    received_at: datetime | None = None,
) -> None:
    """Record an accepted sync only after its database transaction commits."""
    accepted_at = received_at or timezone.now()
    cache_key = _cache_key(station_id)

    def store_presence() -> None:
        try:
            cache.set(
                cache_key,
                accepted_at.isoformat(),
                timeout=PRESENCE_RETENTION_SECONDS,
            )
        except _CACHE_ERRORS as exc:
            logger.warning(
                "Player v2 station presence cache is unavailable for a write (%s).",
                type(exc).__name__,
            )

    transaction.on_commit(store_presence)
