"""Delivery, historical on-air evidence and fresh current playback are distinct."""

from datetime import datetime

from django.db.models import Exists, F, OuterRef, Subquery
from django.utils import timezone

from nomenclatures.player_v2.playback.models import PlaybackEvent
from nomenclatures.player_v2.runtime.service import FRESH_SECONDS, load_runtime_documents
from orders.models import OrderStationState


def confirm_on_air_revisions(order_ids):
    """Mark a revision as having actually started, never as permanently playing."""
    starts = PlaybackEvent.objects.filter(
        order_id=OuterRef("order_id"), nomenclature_id=OuterRef("nomenclature_id"),
        order_revision=OuterRef("desired_revision"), event_type="started", event_sequence=1,
    )
    OrderStationState.objects.filter(
        order_id__in=order_ids, desired_action="apply", status="applied",
        applied_revision=F("desired_revision"), order__revision=F("desired_revision"),
    ).annotate(has_started=Exists(starts)).filter(has_started=True).exclude(
        on_air_revision=F("applied_revision"),
    ).update(on_air_revision=F("applied_revision"))


_NOT_LOADED = object()


def with_playback_evidence(queryset):
    events = PlaybackEvent.objects.filter(
        order_id=OuterRef("pk"), nomenclature_id=OuterRef("nomenclature_id"),
        order_revision=OuterRef("revision"),
    ).order_by("-received_at", "-event_sequence")
    return queryset.annotate(
        _last_playback_kind=Subquery(events.values("event_type")[:1]),
        _last_playback_reason=Subquery(events.values("reason")[:1]),
    )


def actual_order_state(order, document=_NOT_LOADED):
    result = {"code": "unknown", "label": "Состояние эфира неизвестно", "revision": order.revision}
    try:
        delivery = order.station_state
    except OrderStationState.DoesNotExist:
        return result
    if delivery.status == "cancelled" or order.status == 3:
        return {**result, "code": "cancelled", "label": "Отменён"}
    if delivery.desired_action == "cancel":
        return {**result, "code": "cancelling", "label": "Отмена ожидает подтверждения"}
    if delivery.status == "failed":
        return {**result, "code": "delivery_error", "label": "Ошибка доставки или применения", "error": delivery.last_error}
    if delivery.desired_revision != order.revision or delivery.applied_revision != order.revision:
        return {**result, "code": "pending", "label": "Редакция ещё не применена Player"}
    if document is _NOT_LOADED:
        document = load_runtime_documents([order.nomenclature_id]).get(str(order.nomenclature_id))
    if not isinstance(document, dict) or document.get("transport") == "legacy":
        return result
    try:
        age = (timezone.now() - datetime.fromisoformat(document["received_at"])).total_seconds()
    except (KeyError, TypeError, ValueError):
        return result
    if age < 0 or age > FRESH_SECONDS:
        return result
    runtime = document.get("state", {})
    current = list(runtime.get("background", []))
    if isinstance(runtime.get("current_ad"), dict):
        current.append(runtime["current_ad"])
    matches = [item for item in current if isinstance(item, dict)
               and str(item.get("order_id")) == str(order.pk)
               and type(item.get("order_revision")) is int and item["order_revision"] == order.revision]
    if matches:
        if delivery.on_air_revision != order.revision:
            return {**result, "code": "awaiting_fact", "label": "Ожидает подтверждённого события запуска"}
        if runtime.get("maintenance_mode") is True or all(item.get("status") in ("пауза", "paused") for item in matches):
            return {**result, "code": "paused", "label": "На паузе"}
        if any(item.get("status") in ("играет", "playing") for item in matches) or runtime.get("mode") == "ad" and runtime.get("current_ad") in matches:
            return {**result, "code": "on_air", "label": "Сейчас воспроизводится"}
    # No exact revision on an older Player cannot prove that it is off air.
    if any(str(item.get("order_id")) == str(order.pk) for item in current if isinstance(item, dict)):
        return result
    if getattr(order, "_last_playback_kind", None) == "error":
        return {**result, "code": "playback_error", "label": "Последний подтверждённый выход с ошибкой",
                "error": getattr(order, "_last_playback_reason", None)}
    return {**result, "code": "off_air", "label": "Готов, сейчас не воспроизводится"}
