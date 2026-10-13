"""Transactional mutations for legacy and structured playlist content."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterator, Sequence
from typing import TypedDict

from django.core.exceptions import ValidationError

from files.models import File, Playlist, PlaylistItem, PlaylistItemVisual


class ResolvedPlaylistItem(TypedDict):
    """Validated playlist input resolved to model instances."""

    file: File
    images: list[File]


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
    """Reject a full structured edit while legacy orders use the playlist.

    The caller must lock ``playlist`` and own ``transaction.atomic()``. Legacy
    add/remove endpoints have their own replication protocol and deliberately do
    not use this guard.
    """

    if _active_legacy_orders(playlist):
        raise ValidationError(_STRUCTURED_LEGACY_ERROR)


def _ensure_can_be_empty(playlist: Playlist, has_primary_files: bool) -> None:
    if not has_primary_files and _has_active_orders(playlist):
        raise ValidationError(_EMPTY_PLAYLIST_ERROR)


def _temporary_positions(
    positions: Sequence[int], target_count: int
) -> Iterator[int]:
    # Avoid overflow when an old manually assigned position is near int32 max.
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


def _replace_visuals(
    playlist_item: PlaylistItem,
    images: Sequence[File],
    existing: Sequence[PlaylistItemVisual],
) -> None:
    """Keep matching visual occurrences, including their duration and PK."""

    available: dict[object, deque[PlaylistItemVisual]] = defaultdict(deque)
    for visual in existing:
        available[visual.file_id].append(visual)

    if existing:
        for visual, position in zip(existing, _temporary_positions([visual.position for visual in existing], len(images))):
            visual.position = position
        PlaylistItemVisual.objects.bulk_update(existing, ("position",))

    retained: list[PlaylistItemVisual] = []
    additions: list[PlaylistItemVisual] = []
    for position, image in enumerate(images):
        matching = available[image.pk]
        if matching:
            visual = matching.popleft()
            visual.position = position
            retained.append(visual)
        else:
            additions.append(
                PlaylistItemVisual(
                    playlist_item=playlist_item,
                    file=image,
                    position=position,
                )
            )

    removed_ids = [visual.pk for rows in available.values() for visual in rows]
    if removed_ids:
        PlaylistItemVisual.objects.filter(pk__in=removed_ids).delete()
    if additions:
        PlaylistItemVisual.objects.bulk_create(additions)
    if retained:
        PlaylistItemVisual.objects.bulk_update(retained, ("position",))


def _sync_primary_items(
    playlist: Playlist,
    primary_files: Sequence[File],
    images_by_file: dict[object, Sequence[File]] | None,
) -> None:
    existing = list(
        PlaylistItem.objects.select_for_update()
        .filter(playlist=playlist)
        .order_by("position", "pk")
    )
    visuals_by_item: dict[int, list[PlaylistItemVisual]] = defaultdict(list)
    if images_by_file is not None:
        visuals = (
            PlaylistItemVisual.objects.select_for_update()
            .filter(playlist_item__playlist=playlist)
            .order_by("playlist_item_id", "position", "pk")
        )
        for visual in visuals:
            visuals_by_item[visual.playlist_item_id].append(visual)
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
        if images_by_file is not None:
            _replace_visuals(
                item,
                images_by_file[file.pk],
                visuals_by_item[item.pk],
            )

    if additions:
        PlaylistItem.objects.bulk_create(additions)
        if images_by_file is not None:
            created = {
                item.file_id: item
                for item in PlaylistItem.objects.filter(
                    playlist=playlist,
                    file_id__in=[item.file_id for item in additions],
                )
            }
            visuals = [
                PlaylistItemVisual(
                    playlist_item=created[file.pk],
                    file=image,
                    position=position,
                )
                for file in primary_files
                if file.pk in created
                for position, image in enumerate(images_by_file[file.pk])
            ]
            if visuals:
                PlaylistItemVisual.objects.bulk_create(visuals)
    if retained:
        PlaylistItem.objects.bulk_update(retained, ("position",))

    playlist.files.set(primary_files)


def replace_playlist_items(
    playlist: Playlist, resolved_items: Sequence[ResolvedPlaylistItem]
) -> None:
    """Replace ordered structured content while retaining matching row IDs.

    ``resolved_items`` must already be validated and resolved by the API input
    boundary. The caller must lock ``playlist`` and own
    ``transaction.atomic()`` so graph changes and order refreshes roll back
    together.
    """

    ensure_structured_editable(playlist)
    primary_files = [item["file"] for item in resolved_items]
    if len({file.pk for file in primary_files}) != len(primary_files):
        raise ValidationError("Основной файл не должен повторяться в плейлисте.")
    _ensure_can_be_empty(playlist, bool(primary_files))
    images_by_file = {
        item["file"].pk: item["images"] for item in resolved_items
    }
    _sync_primary_items(playlist, primary_files, images_by_file)


def set_playlist_files(
    playlist: Playlist, ordered_files: Sequence[File]
) -> None:
    """Set primary files and adapt a structured graph only when it exists.

    A legacy playlist without ``PlaylistItem`` rows stays legacy. The caller
    must lock ``playlist`` and own ``transaction.atomic()``.
    """

    primary_files = list(ordered_files)
    if len({file.pk for file in primary_files}) != len(primary_files):
        raise ValidationError("Основной файл не должен повторяться в плейлисте.")
    _ensure_can_be_empty(playlist, bool(primary_files))
    if not PlaylistItem.objects.filter(playlist=playlist).exists():
        playlist.files.set(primary_files)
        return
    _sync_primary_items(playlist, primary_files, images_by_file=None)


def refresh_playlist_orders(playlist: Playlist) -> list[object]:
    """Increment and enqueue every active unified order in stable lock order.

    The caller decides whether composition changed. It must own
    ``transaction.atomic()``; database commands produced by ``enqueue_order``
    then roll back with the playlist and revisions if any refresh fails.
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
