"""Bounded delivery observations live in the existing pending command journal."""

from datetime import datetime

from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.utils import timezone

from nomenclatures.models import StationCommandV2
from orders.models import OrderStationState


PHASE_LABELS = {
    "downloading": "Загрузка файлов",
    "verifying": "Проверка файлов",
    "applying": "Применение расписания",
}
FRESH_SECONDS = 45
CHECKPOINT_SECONDS = 10


@transaction.atomic
def store_order_progress(credential, reports, received_at):
    """Run after receipt commit, locking command rows in a stable order."""
    reports_by_id = {report["command_id"]: report for report in reports}
    commands = StationCommandV2.objects.select_for_update().filter(
        nomenclature_id=credential.nomenclature_id, command_id__in=reports_by_id,
        kind="apply_order_manifest", status=StationCommandV2.Status.PENDING,
    ).order_by("command_id")
    for command in commands:
        report = reports_by_id[command.command_id]
        if command.expires_at and command.expires_at <= received_at:
            continue
        body = command.body
        if body.get("revision") != report["revision"] or len(body.get("files", [])) != report["files_total"]:
            continue
        # Read without another row lock: command lock fences enqueue/receipt,
        # and avoids reversing their order -> state -> command lock ordering.
        if not OrderStationState.objects.filter(
            command_id=command.command_id, nomenclature_id=credential.nomenclature_id,
            order_id=body.get("order_id"), desired_revision=report["revision"], desired_action="apply",
            order__revision=report["revision"],
        ).exists():
            continue
        values = {key: report[key] for key in ("revision", "phase", "files_verified", "files_total")}
        old = (command.result or {}).get("order_progress", {})
        if old.get("received_at") and datetime.fromisoformat(old["received_at"]) > received_at:
            continue
        same = all(old.get(key) == value for key, value in values.items())
        if same and (received_at - command.updated_at).total_seconds() < CHECKPOINT_SECONDS:
            continue
        command.result = {"order_progress": {**values, "received_at": received_at.isoformat()}}
        command.save(update_fields=("result", "updated_at"))


def with_order_progress(queryset):
    command = StationCommandV2.objects.filter(
        command_id=OuterRef("station_state__command_id"), nomenclature_id=OuterRef("nomenclature_id"),
        kind="apply_order_manifest", status="pending",
    )
    return queryset.annotate(_delivery_result=Subquery(command.values("result")[:1]))


def delivery_progress(order):
    """Return an observation, explicitly stale after a missing heartbeat."""
    try:
        state = order.station_state
    except OrderStationState.DoesNotExist:
        return None
    if (state.status not in ("queued", "delivered") or state.desired_action != "apply"
            or state.desired_revision != order.revision):
        return None
    if hasattr(order, "_delivery_result"):
        result = order._delivery_result
    else:
        result = StationCommandV2.objects.filter(
            command_id=state.command_id, nomenclature_id=order.nomenclature_id,
            kind="apply_order_manifest", status="pending",
        ).values_list("result", flat=True).first()
    progress = (result or {}).get("order_progress")
    if not isinstance(progress, dict) or progress.get("revision") != order.revision:
        return None
    try:
        age = (timezone.now() - datetime.fromisoformat(progress["received_at"])).total_seconds()
    except (KeyError, TypeError, ValueError):
        return None
    fresh = 0 <= age <= FRESH_SECONDS
    return {**progress, "fresh": fresh, "label": PHASE_LABELS.get(progress.get("phase"), "Обработка заказа"),
            "received_at": datetime.fromisoformat(progress["received_at"]).strftime("%Y-%m-%d %H:%M:%S")}
