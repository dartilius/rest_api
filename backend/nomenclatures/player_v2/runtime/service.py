"""Ordered live snapshots, bounded Redis cache, and a PostgreSQL reserve."""

from copy import deepcopy
from datetime import datetime
import logging
import time
from uuid import NAMESPACE_DNS, uuid5

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db import DatabaseError, transaction
from django.utils import timezone
from django_redis.exceptions import ConnectionInterrupted
from redis.exceptions import RedisError

from nomenclatures.player_v2.runtime.models import StationRuntimeSnapshot
from nomenclatures.player_v2.runtime.presentation import broadcast_context


logger = logging.getLogger(__name__)
CACHE_ERRORS = (ConnectionInterrupted, RedisError, OSError)
RETENTION = 7 * 24 * 60 * 60
PERSIST_SECONDS = 30
FRESH_SECONDS = 45


def runtime_group(station_id):
    return f"station.runtime.{str(station_id).replace('-', '')}"


def _key(station_id):
    return f"station-runtime:v1:{station_id}"


def _document(row):
    return {
        "state": row.state, "actors": row.actors,
        "received_at": row.received_at.isoformat(), "transport": row.transport,
        "persisted_at": row.received_at.isoformat(),
        "frame_id": row.frame_id,
    }


def _read(station_id):
    try:
        value = cache.get(_key(station_id))
    except CACHE_ERRORS:
        value = None
    if (isinstance(value, dict) and isinstance(value.get("received_at"), str)
            and isinstance(value.get("state"), dict) and isinstance(value.get("actors"), dict)):
        return value
    row = StationRuntimeSnapshot.objects.filter(nomenclature_id=station_id).first()
    return _document(row) if row else None


def load_runtime_documents(station_ids):
    ids = list(dict.fromkeys(str(value) for value in station_ids))
    if not ids:
        return {}
    try:
        cached = cache.get_many([_key(value) for value in ids]) or {}
    except CACHE_ERRORS:
        cached = {}
    result = {value: cached.get(_key(value)) for value in ids}
    missing = [value for value in ids if not isinstance(result[value], dict)]
    for row in StationRuntimeSnapshot.objects.filter(nomenclature_id__in=missing):
        result[str(row.nomenclature_id)] = _document(row)
    return result


def _elapsed(value, now):
    try:
        received = datetime.fromisoformat(value)
        return (now - received).total_seconds()
    except (TypeError, ValueError):
        return float("inf")


def display_snapshot(station_id, *, legacy_state=None, legacy_received=None):
    document = _read(station_id)
    if document is None:
        document = {"state": legacy_state or {}, "transport": "legacy",
                    "received_at": legacy_received.isoformat() if legacy_received else None}
    age = _elapsed(document.get("received_at"), timezone.now())
    received_text = ""
    try:
        received_text = datetime.fromisoformat(document["received_at"]).strftime("%d.%m.%Y %H:%M:%S")
    except (TypeError, ValueError):
        pass
    fresh_for = 90 if document.get("transport") == "legacy" else FRESH_SECONDS
    return {
        "type": "runtime", "content": broadcast_context(document["state"]),
        "received_at": received_text,
        "version": document.get("frame_id") or document.get("received_at"),
        "stale": age < 0 or age > fresh_for,
        "source": document.get("transport", "unknown"),
    }


def _advance(document, actor, frame):
    actors = deepcopy(document.get("actors", {})) if document else {}
    previous = actors.get(actor)
    stream = str(frame["stream_id"])
    sequence = frame["sequence"]
    changed_stream = previous is None or previous["stream_id"] != stream
    if previous:
        if stream in previous.get("retired", []):
            return None
        if not changed_stream and sequence <= previous["sequence"]:
            return None
    retired = list(previous.get("retired", [])) if previous else []
    if previous and changed_stream:
        retired.append(previous["stream_id"])
    actors[actor] = {"stream_id": stream, "sequence": sequence, "retired": retired[-32:]}
    # A point normally has one installation; keep history bounded for a fleet.
    if len(actors) > 64:
        actors.pop(next(key for key in actors if key != actor))
    return actors, changed_stream


def _critical(state):
    result = deepcopy(state)
    for item in result.get("background", []):
        item.pop("position_ms", None)
    ad = result.get("current_ad")
    if isinstance(ad, dict):
        ad.pop("position_ms", None)
    return result


def _broadcast(station_id):
    try:
        layer = get_channel_layer()
        if layer is not None:
            async_to_sync(layer.group_send)(runtime_group(station_id), {"type": "runtime.changed"})
    except CACHE_ERRORS:
        logger.warning("Runtime fan-out unavailable; viewers can poll.")


def _persist(station_id, document):
    StationRuntimeSnapshot.objects.update_or_create(nomenclature_id=station_id, defaults={
        "state": document["state"], "actors": document["actors"],
        "received_at": datetime.fromisoformat(document["received_at"]),
        "transport": document["transport"],
        "frame_id": document["frame_id"],
    })


def accept_runtime(credential, frame, *, transport):
    """A token's station is authoritative; stream sequences fence delayed frames."""
    station_id = credential.nomenclature_id
    if not type(credential).objects.filter(
        pk=credential.pk, is_active=True, token_hash=credential.token_hash,
        nomenclature_id=station_id,
    ).exists():
        return {"accepted": False, "code": "credential_revoked"}
    actor = f"{credential._meta.model_name}:{credential.pk}"
    return _accept(station_id, actor, frame, transport)


def _accept(station_id, actor, frame, transport):
    now = timezone.now()
    try:
        with cache.lock(f"{_key(station_id)}:lock", timeout=10, blocking_timeout=1):
            old = _read(station_id)
            advanced = _advance(old, actor, frame)
            if advanced is None:
                return {"accepted": False, "code": "stale_sequence"}
            actors, changed_stream = advanced
            document = {"state": frame["state"], "actors": actors,
                        "received_at": now.isoformat(), "transport": transport,
                        "frame_id": f"{frame['stream_id']}:{frame['sequence']}",
                        "persisted_at": old.get("persisted_at") if old else None}
            if changed_stream or old is None or _critical(old["state"]) != _critical(frame["state"]) or _elapsed(document["persisted_at"], now) >= PERSIST_SECONDS:
                _persist(station_id, document)
                document["persisted_at"] = now.isoformat()
            cache.set(_key(station_id), document, timeout=RETENTION)
            if cache.get(_key(station_id)) != document:
                raise ConnectionError("Runtime cache did not acknowledge its write")
    except CACHE_ERRORS:
        # Redis loss must not disable current-state monitoring. A row lock
        # preserves ordering while HTTP/browser polling uses PostgreSQL.
        with transaction.atomic():
            row, _created = StationRuntimeSnapshot.objects.get_or_create(nomenclature_id=station_id, defaults={
                "state": {}, "actors": {}, "received_at": now, "transport": transport,
            })
            row = StationRuntimeSnapshot.objects.select_for_update().get(pk=row.pk)
            old = _document(row)
            advanced = _advance(old, actor, frame)
            if advanced is None:
                return {"accepted": False, "code": "stale_sequence"}
            document = {"state": frame["state"], "actors": advanced[0],
                        "received_at": now.isoformat(), "transport": transport,
                        "frame_id": f"{frame['stream_id']}:{frame['sequence']}"}
            _persist(station_id, document)
    _broadcast(station_id)
    return {"accepted": True, "sequence": frame["sequence"], "stream_id": str(frame["stream_id"])}


def publish_legacy_runtime(station_id, state):
    try:
        _publish_legacy_runtime(station_id, state)
    except (DatabaseError, *CACHE_ERRORS):
        logger.warning("Legacy runtime relay unavailable; existing legacy response is preserved.")


def _publish_legacy_runtime(station_id, state):
    """Reuse a legacy heartbeat without allowing it to replace fresh v2 data."""
    old = _read(station_id)
    if old and old.get("transport") != "legacy" and _elapsed(old["received_at"], timezone.now()) <= FRESH_SECONDS:
        return
    from nomenclatures.player_v2.runtime.serializers import RuntimeStateSerializer
    if not isinstance(state, dict):
        return
    def item(value):
        result = {key: value[key] for key in ("name", "type", "status", "order_id", "order_revision") if key in value and value[key] is not None}
        for field in ("duration", "position"):
            amount = value.get(field + "_ms", value.get(field))
            if amount is not None:
                result[field + "_ms"] = amount
        if "duration_ms" not in result and "duration_seconds" in value:
            result["duration_ms"] = value["duration_seconds"]
        return result
    ad = state.get("current_ad")
    backgrounds = state.get("background")
    normalized = {
        "mode": state.get("mode", "unknown"), "maintenance_mode": state.get("maintenance_mode", False),
        "current_ad": item(ad) if isinstance(ad, dict) and ad else None,
        "background": [item(value) for value in backgrounds if isinstance(value, dict)] if isinstance(backgrounds, list) else [],
    }
    serializer = RuntimeStateSerializer(data=normalized)
    if serializer.is_valid():
        _accept(station_id, "legacy", {
            "stream_id": uuid5(NAMESPACE_DNS, f"rmc-legacy:{station_id}"),
            "sequence": time.time_ns(), "state": serializer.validated_data,
        }, "legacy")
