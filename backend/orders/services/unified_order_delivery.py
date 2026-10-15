"""Delivery of unified orders to either v2 Player or the legacy adapter."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from nomenclatures.models import StationCommandV2
from nomenclatures.player_v2.sync_state import station_protocol
from orders.models import Order, OrderStationState
from orders.services.order_audio_images import (
    public_order_parameters,
    resolve_order_audio_image_files,
)
from tasks.models import Task


AD_POLICY_TO_TASK_TYPE = {
    "workday": 0, "hourly_slots": 0, "open_offset": 1, "close_offset": 2,
    "fixed_time": 3, "open_to_fixed": 4, "fixed_to_close": 5,
    "start_to_close": 5, "event": 6, "continuous": 7,
}


def requires_continuous_advertising(order: Order) -> bool:
    return order.placement == "advertising" and order.playback_policy == "continuous"


def requires_order_schedule(order: Order) -> bool:
    """Weekday schedules must never leak to a Player that ignores them."""
    parameters = order.parameters or {}
    weekdays = parameters.get("weekdays")
    return "weekdays" in parameters and not (
        isinstance(weekdays, list)
        and len(weekdays) == 7
        and all(type(day) is int for day in weekdays)
        and set(weekdays) == set(range(7))
    )


def validate_order_schedule(order: Order) -> None:
    if not requires_order_schedule(order):
        return
    protocol = station_protocol(order.nomenclature)
    if (
        type(protocol.get("unified_orders_version")) is not int
        or protocol.get("unified_orders_version") != 1
        or type(protocol.get("order_schedule_version")) is not int
        or protocol.get("order_schedule_version") != 1
    ):
        raise ValidationError(
            "Обновите Player точки: выбранные дни недели поддерживаются протоколом расписания заказов версии 1."
        )


def validate_continuous_advertising(order: Order) -> None:
    if not requires_continuous_advertising(order):
        return
    protocol = station_protocol(order.nomenclature)
    version = protocol.get("continuous_advertising_version")
    if type(version) is not int or version != 1 or protocol.get("unified_orders_version") != 1:
        raise ValidationError("Обновите Player точки для непрерывной рекламы вместо фона.")


def requires_advertising_options(order: Order) -> bool:
    """Old Players always suppress both backgrounds and do not mute ads."""
    return order.placement == "advertising" and (
        not getattr(order, "suppress_background_audio", False)
        or not getattr(order, "suppress_background_visual", False)
        or (order.parameters or {}).get("audio_muted", False)
    )


def validate_advertising_options(order: Order) -> None:
    if not requires_advertising_options(order):
        return
    version = station_protocol(order.nomenclature).get("advertising_options_version")
    if type(version) is not int or version != 1:
        raise ValidationError(
            "Player этой точки ещё не поддерживает настройки фона и звука рекламы. "
            "Обновите Player или включите подавление обоих видов фона без audio_muted."
        )


def _format_local_datetime(value):
    if value is None:
        return None
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _playlist_payload(order: Order) -> tuple[list[dict[str, object]], dict[str, list[str]], list[object]]:
    items = list(order.playlist.items.select_related("file"))
    if not items:
        legacy_files = list(order.playlist.files.all())
        if not legacy_files:
            raise ValidationError("Плейлист заказа не содержит файлов.")
        files = [{"id": str(file.id), "hash": file.hash} for file in legacy_files]
        media_files = legacy_files
    else:
        files = [
            {"id": str(item.file_id), "hash": item.file.hash}
            for item in items
        ]
        media_files = [item.file for item in items]

    if order.placement != "advertising":
        return files, {}, media_files
    slides, image_files = resolve_order_audio_image_files(order)
    return files, slides, [*media_files, *image_files]


def requires_visual_queue(order: Order) -> bool:
    if order.placement != "background":
        return False
    types = set(order.playlist.items.values_list("file__type", flat=True))
    if not types:
        types = set(order.playlist.files.values_list("type", flat=True))
    return bool(types) and types <= {1, 2} and (
        order.is_permanent or len(types) > 1 or "weight" in (order.parameters or {})
        or "image_duration_seconds" in (order.parameters or {})
    )


def validate_visual_queue(order: Order) -> None:
    if not requires_visual_queue(order):
        return
    protocol = station_protocol(order.nomenclature)
    version = protocol.get("background_visual_queue_version")
    if type(version) is not int or version != 1:
        raise ValidationError("Обновите Player точки для смешанного визуального плейлиста, веса и времени показа картинок.")


def _background_type(order: Order) -> int:
    item_types = list(order.playlist.items.select_related("file").values_list("file__type", flat=True))
    if not item_types:
        item_types = list(order.playlist.files.values_list("type", flat=True))
    if set(item_types) == {1, 2}:
        return 1
    if not item_types or len(set(item_types)) != 1 or item_types[0] not in {0, 1, 2, 3}:
        raise ValidationError("Фоновый плейлист должен содержать файлы одного типа: музыка, видео, картинки или тикер.")
    return item_types[0]


def build_task(order: Order) -> Task:
    """Build a legacy-compatible task without saving it."""
    validate_order_schedule(order)
    validate_continuous_advertising(order)
    validate_advertising_options(order)
    validate_visual_queue(order)
    files, slides, media_files = _playlist_payload(order)
    if order.placement == "advertising":
        try:
            broadcast_type = AD_POLICY_TO_TASK_TYPE[order.playback_policy]
        except KeyError as exc:
            raise ValidationError("Выбранное правило недоступно для рекламного заказа.") from exc
        order_parameters = public_order_parameters(order.parameters)
        order_parameters.update({
            "suppress_background_audio": getattr(order, "suppress_background_audio", False),
            "suppress_background_visual": getattr(order, "suppress_background_visual", False),
            "audio_muted": order_parameters.get("audio_muted", False),
        })
        if requires_continuous_advertising(order):
            if any(file.type not in (0, 1, 2) for file in media_files):
                raise ValidationError("Непрерывная реклама поддерживает музыку, видео и картинки, без тикеров.")
            order_parameters.pop("times_in_hour", None)
            order_parameters["suppress_background_audio"] = not order_parameters["audio_muted"]
            order_parameters["suppress_background_visual"] = True
        if order.playback_policy == "start_to_close":
            order_parameters["schedule_mode"] = "start_to_close"
        else:
            order_parameters.pop("schedule_mode", None)
        return Task(owner=order.owner, client=order.nomenclature, type=4, parameters={
            "order_id": str(order.id), "order_parameters": order_parameters,
            "broadcast_type": broadcast_type, "broadcast_start": _format_local_datetime(order.starts_at),
            "broadcast_end": _format_local_datetime(order.ends_at),
            "playlist": {"id": str(order.playlist_id), "files": files, "slides": slides or None},
            "revision": order.revision,
        })
    background_type = _background_type(order)
    if requires_visual_queue(order):
        item_types = dict(order.playlist.items.values_list("file_id", "file__type"))
        if not item_types:
            item_types = dict(order.playlist.files.values_list("id", "type"))
        item_types = {str(key): value for key, value in item_types.items()}
        for file in files:
            file["media_type"] = item_types[file["id"]]
            if file["media_type"] == 2 and "image_duration_seconds" in (order.parameters or {}):
                file["duration_seconds"] = order.parameters["image_duration_seconds"]
    parameters = public_order_parameters(order.parameters)
    if order.is_permanent and background_type in (1, 2) and order.created is not None:
        # Stable generation across resends/revisions, independent of arrival order.
        parameters["permanent_generation"] = order.created.isoformat(timespec="microseconds")
    return Task(owner=order.owner, client=order.nomenclature, type=background_type, parameters={
        "order_id": str(order.id), "order_type": background_type, "is_permanent": order.is_permanent,
        "broadcast_start": _format_local_datetime(order.starts_at or order.created), "broadcast_end": _format_local_datetime(order.ends_at),
        "playlist": {"id": str(order.playlist_id), "files": files}, "revision": order.revision,
        "parameters": parameters,
    })


def _supports_v2_orders(order: Order) -> bool:
    protocol = station_protocol(order.nomenclature)
    return (
        requires_order_schedule(order)
        or protocol.get("unified_orders_version") == 1
        or OrderStationState.objects.filter(order=order).exists()
    )


def validate_order_delivery(order: Order) -> None:
    """Validate delivery before accepting an admin form, without creating commands."""
    build_task(order)
    if _supports_v2_orders(order):
        _media_manifest(order)


def _media_manifest(order: Order) -> list[dict[str, object]]:
    _, _, source_files = _playlist_payload(order)
    seen, manifest = set(), []
    for file in source_files:
        if file.pk in seen:
            continue
        seen.add(file.pk)
        if not file.sha256hash or file.size < 0:
            raise ValidationError(f"У файла {file!s} отсутствуют проверяемые метаданные для Player v2.")
        manifest.append({"id": str(file.pk), "name": file.name, "size": file.size,
                         "sha256": file.sha256hash, "hash": file.hash, "url": file.url})
    return manifest


def _enqueue_v2(order: Order, *, action: str) -> StationCommandV2:
    """Persist a complete revision snapshot; it must run inside a transaction."""
    Order.objects.select_for_update().get(pk=order.pk)
    state, _ = OrderStationState.objects.select_for_update().get_or_create(
        order=order, defaults={"nomenclature": order.nomenclature, "desired_revision": order.revision},
    )
    if state.command_id:
        StationCommandV2.objects.filter(command_id=state.command_id, status=StationCommandV2.Status.PENDING).update(
            status=StationCommandV2.Status.SUPERSEDED
        )
    body: dict[str, object] = {"order_id": str(order.pk), "revision": order.revision, "action": action, "placement": order.placement}
    kind = "cancel_order" if action == OrderStationState.Action.CANCEL else "apply_order_manifest"
    if action == OrderStationState.Action.APPLY:
        task = build_task(order)
        body.update({"task": {"task_type": task.type, "parameters": task.parameters}, "files": _media_manifest(order)})
        if requires_advertising_options(order):
            body["requires_advertising_options_version"] = 1
        if requires_continuous_advertising(order):
            body["requires_continuous_advertising_version"] = 1
        if requires_order_schedule(order):
            body["requires_order_schedule_version"] = 1
        if requires_visual_queue(order):
            body["requires_background_visual_queue_version"] = 1
            if order.is_permanent:
                previous = Order.objects.filter(
                    nomenclature=order.nomenclature, placement="background", is_permanent=True,
                    status__in=(0, 1), created__lt=order.created,
                ).select_related("playlist").prefetch_related(
                    "playlist__items__file", "playlist__files",
                ).exclude(pk=order.pk)
                body["replaces_permanent_visual"] = [
                    {"order_id": str(item.pk), "revision": item.revision}
                    for item in previous if _is_visual_playlist(item.playlist)
                ]
    else:
        previous = StationCommandV2.objects.filter(command_id=state.command_id).first() if state.command_id else None
        previous_body = previous.body if previous else {}
        if previous_body.get("task_type") in (5, 6, 7, 8, 9):
            body["task_type"] = previous_body["task_type"]
        else:
            previous_type = (previous_body.get("task") or {}).get("task_type")
            background_type = previous_type if previous_type in (0, 1, 2, 3) else None
            body["task_type"] = 9 if order.placement == "advertising" else {0: 5, 1: 6, 2: 7, 3: 8}[background_type if background_type is not None else _background_type(order)]
    command = StationCommandV2.objects.create(nomenclature=order.nomenclature, kind=kind, body=body)
    state.nomenclature, state.desired_action, state.desired_revision = order.nomenclature, action, order.revision
    state.status, state.command_id, state.last_error = OrderStationState.Status.QUEUED, command.command_id, ""
    state.save(update_fields=("nomenclature", "desired_action", "desired_revision", "status", "command_id", "last_error", "updated_at"))
    return command


def refresh_manifest_urls(body):
    """Refresh expiring links without changing the immutable media snapshot."""
    from files.models import File
    payload = dict(body)
    manifest = [dict(item) for item in payload.get("files", [])]
    current = {str(item.pk): item for item in File.objects.filter(pk__in=[item["id"] for item in manifest])}
    for item in manifest:
        file = current.get(item["id"])
        if file is not None and file.sha256hash == item["sha256"] and file.size == item["size"]:
            item["url"] = file.url
    payload["files"] = manifest
    return payload


def enqueue_order(order: Order):
    """Create exactly one command for this order's explicitly advertised capability."""
    with transaction.atomic():
        validate_advertising_options(order)
        if _supports_v2_orders(order):
            return _enqueue_v2(order, action=OrderStationState.Action.APPLY)
        task = build_task(order)
        task.save()
        return task


def enqueue_cancellation(order: Order):
    """Cancel by immutable revision; legacy media type is resolved immediately."""
    with transaction.atomic():
        if _supports_v2_orders(order):
            return _enqueue_v2(order, action=OrderStationState.Action.CANCEL)
        task_type = 9 if order.placement == "advertising" else {0: 5, 1: 6, 2: 7, 3: 8}[_background_type(order)]
        return Task.objects.create(owner=order.owner, client=order.nomenclature, type=task_type,
                                   parameters={"order_id": str(order.id), "revision": order.revision})


def cancel_replaced_visual_orders(command, result) -> None:
    """Cancel only the predecessor revisions captured in this applied snapshot."""
    if result.get("replacement_ready") is not True or result.get("replacement_group") != "visual":
        return
    body = command.body
    if body.get("requires_background_visual_queue_version") != 1:
        return
    for previous in body.get("replaces_permanent_visual", []):
        order = Order.objects.select_for_update().filter(
            pk=previous["order_id"], revision=previous["revision"],
            nomenclature=command.nomenclature, placement="background", is_permanent=True,
            status__in=(0, 1),
        ).first()
        if order is None:
            continue
        state = OrderStationState.objects.filter(order=order).first()
        if state is not None and state.desired_action == OrderStationState.Action.CANCEL:
            continue
        order.revision += 1
        order.is_active = False
        order.save(update_fields=("revision", "is_active"))
        enqueue_cancellation(order)


def _is_visual_playlist(playlist) -> bool:
    items = list(playlist.items.all())
    types = {item.file.type for item in items} if items else {file.type for file in playlist.files.all()}
    return bool(types) and types <= {1, 2}
