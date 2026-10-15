"""Атомарное изменение основных файлов плейлиста."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TypedDict

from django.core.exceptions import ValidationError

from files.models import File, Playlist, PlaylistItem, PlaylistItemVisual


class ResolvedPlaylistItem(TypedDict):
    """Проверенные основные файлы плейлиста."""

    file: File


_ACTIVE_STATUSES = (0, 1)
_EMPTY_PLAYLIST_ERROR = (
    "Сначала отмените активные заказы, затем можно очистить плейлист."
)
_STRUCTURED_LEGACY_ERROR = (
    "Нельзя полностью изменить состав плейлиста, пока он используется в старых "
    "активных заказах. Сначала отмените активные заказы."
)


def _active_legacy_orders(playlist: Playlist) -> bool:
    from orders.models import AdOrder, BgOrder

    common = {
        "playlist": playlist,
        "is_active": True,
        "status__in": _ACTIVE_STATUSES,
    }
    return (
        AdOrder.objects.filter(**common).exists()
        or BgOrder.objects.filter(**common).exists()
    )


def _has_active_orders(playlist: Playlist) -> bool:
    from orders.models import Order

    return (
        Order.objects.filter(
            playlist=playlist,
            is_active=True,
            status__in=_ACTIVE_STATUSES,
        ).exists()
        or _active_legacy_orders(playlist)
    )


def ensure_structured_editable(playlist: Playlist) -> None:
    """Не заменяем полностью состав, пока плейлист используется legacy-заказами.

    Вызывающий код блокирует плейлист внутри transaction.atomic(). Старые
    add/remove сохраняют собственный протокол доставки изменений.
    """

    if _active_legacy_orders(playlist):
        raise ValidationError(_STRUCTURED_LEGACY_ERROR)


def _ensure_can_be_empty(playlist: Playlist, has_primary_files: bool) -> None:
    if not has_primary_files and _has_active_orders(playlist):
        raise ValidationError(_EMPTY_PLAYLIST_ERROR)


def _historical_visuals_error() -> str:
    # Ленивый импорт предотвращает цикл с сервисом админки.
    from files.playlist_admin_service import HISTORICAL_VISUALS_ERROR

    return HISTORICAL_VISUALS_ERROR


def _prune_order_audio_images(
    playlist: Playlist, primary_files: Sequence[File]
) -> None:
    from orders.services.order_audio_images import (
        prune_order_audio_images_for_playlist,
    )

    prune_order_audio_images_for_playlist(
        playlist,
        remaining_primary_ids=(file.pk for file in primary_files),
    )


def _temporary_positions(
    positions: Sequence[int], target_count: int
) -> Iterator[int]:
    # Временные позиции не должны переполняться возле границы int32.
    occupied = set(positions) | set(range(target_count))
    candidate = target_count
    for _ in positions:
        while candidate in occupied:
            candidate += 1
        occupied.add(candidate)
        yield candidate


def _move_items_to_temporary_positions(
    items: Sequence[PlaylistItem], target_count: int
) -> None:
    if not items:
        return
    for item, position in zip(items, _temporary_positions([item.position for item in items], target_count)):
        item.position = position
    PlaylistItem.objects.bulk_update(items, ("position",))


def _sync_primary_items(
    playlist: Playlist,
    primary_files: Sequence[File],
) -> None:
    existing = list(
        PlaylistItem.objects.select_for_update()
        .filter(playlist=playlist)
        .order_by("position", "pk")
    )
    retained_by_file: dict[object, PlaylistItem] = {}
    duplicate_ids: list[int] = []
    for item in existing:
        if item.file_id in retained_by_file:
            duplicate_ids.append(item.pk)
        else:
            retained_by_file[item.file_id] = item

    desired_ids = {file.pk for file in primary_files}
    removed_ids = duplicate_ids + [
        item.pk for file_id, item in retained_by_file.items()
        if file_id not in desired_ids
    ]
    if removed_ids and PlaylistItemVisual.objects.filter(
        playlist_item_id__in=removed_ids
    ).exists():
        raise ValidationError(_historical_visuals_error())

    _move_items_to_temporary_positions(existing, len(primary_files))
    if removed_ids:
        PlaylistItem.objects.filter(pk__in=removed_ids).delete()

    retained: list[PlaylistItem] = []
    additions: list[PlaylistItem] = []
    for position, file in enumerate(primary_files):
        item = retained_by_file.get(file.pk)
        if item is None:
            additions.append(
                PlaylistItem(playlist=playlist, file=file, position=position)
            )
            continue
        item.position = position
        retained.append(item)
    if additions:
        PlaylistItem.objects.bulk_create(additions)
    if retained:
        PlaylistItem.objects.bulk_update(retained, ("position",))

    playlist.files.set(primary_files)
    _prune_order_audio_images(playlist, primary_files)


def replace_playlist_items(
    playlist: Playlist, resolved_items: Sequence[ResolvedPlaylistItem]
) -> None:
    """Обновляем основные файлы и порядок, сохраняя идентификаторы строк.

    Файлы уже проверены сериализатором. Вызывающий код блокирует плейлист
    внутри transaction.atomic(), чтобы состав и отправка заказов откатились вместе.
    """

    ensure_structured_editable(playlist)
    primary_files = [item["file"] for item in resolved_items]
    if len({file.pk for file in primary_files}) != len(primary_files):
        raise ValidationError("Основной файл не должен повторяться в плейлисте.")
    _ensure_can_be_empty(playlist, bool(primary_files))
    _sync_primary_items(playlist, primary_files)


def set_playlist_files(
    playlist: Playlist, ordered_files: Sequence[File]
) -> None:
    """Обновляем файлы; позиции синхронизируем только у структурированного плейлиста.

    Старый плейлист без строк PlaylistItem остаётся в формате M2M.
    Вызывающий код блокирует плейлист внутри transaction.atomic().
    """

    primary_files = list(ordered_files)
    if len({file.pk for file in primary_files}) != len(primary_files):
        raise ValidationError("Основной файл не должен повторяться в плейлисте.")
    _ensure_can_be_empty(playlist, bool(primary_files))
    if not PlaylistItem.objects.filter(playlist=playlist).exists():
        playlist.files.set(primary_files)
        _prune_order_audio_images(playlist, primary_files)
        return
    _sync_primary_items(playlist, primary_files)


def refresh_playlist_orders(playlist: Playlist) -> list[object]:
    """Отправляем новую версию каждому действующему заказу в стабильном порядке.

    Вызывающий код определяет, изменился ли состав, и открывает transaction.atomic().
    Ошибка отправки откатывает изменение плейлиста и версий заказов.
    """

    from orders.models import Order
    from orders.services.unified_order_delivery import enqueue_order

    orders = list(
        Order.objects.select_for_update(of=("self",))
        .filter(
            playlist=playlist,
            is_active=True,
            status__in=_ACTIVE_STATUSES,
        )
        .select_related("nomenclature", "owner", "playlist")
        .order_by("pk")
    )
    commands: list[object] = []
    for order in orders:
        order.revision += 1
        order.save(update_fields=("revision",))
        commands.append(enqueue_order(order))
    return commands
