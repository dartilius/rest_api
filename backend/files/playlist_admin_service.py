"""Atomic playlist graph operations used by Django admin."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from typing import TypedDict

from django.core.exceptions import ValidationError
from django.db import transaction

from files.models import File, Playlist, PlaylistItem, PlaylistItemVisual
from files.playlist_mutations import (
    ensure_structured_editable,
    refresh_playlist_orders,
    replace_playlist_items,
)


logger = logging.getLogger(__name__)


class AdminPlaylistDeliveryError(Exception):
    """A graph edit was rolled back because Player delivery could not refresh."""


class AdminPlaylistItem(TypedDict):
    """One resolved primary file and its ordered visual occurrences."""

    file: File
    images: list[File]
    position: int


def playlist_graph_signature(playlist: Playlist):
    """Return the Player-relevant ordered graph without loading media URLs."""

    items = list(
        PlaylistItem.objects.filter(playlist=playlist)
        .order_by("position", "pk")
        .values_list("pk", "file_id")
    )
    if not items:
        return (
            "files",
            tuple(sorted(str(pk) for pk in playlist.files.values_list("pk", flat=True))),
        )

    visuals: dict[int, list[object]] = {}
    visual_rows = (
        PlaylistItemVisual.objects.filter(playlist_item__playlist=playlist)
        .order_by("playlist_item_id", "position", "pk")
        .values_list("playlist_item_id", "file_id")
    )
    for item_id, file_id in visual_rows:
        visuals.setdefault(item_id, []).append(str(file_id))
    return (
        "items",
        tuple(
            (str(file_id), tuple(visuals.get(item_id, ())))
            for item_id, file_id in items
        ),
    )


def resolved_graph_signature(items: Sequence[AdminPlaylistItem]):
    return (
        "items",
        tuple(
            (
                str(item["file"].pk),
                tuple(str(image.pk) for image in item["images"]),
            )
            for item in items
        ),
    )


def snapshot_playlist_items(playlist: Playlist) -> list[AdminPlaylistItem]:
    """Read the canonical graph, falling back to legacy M2M files."""

    rows = list(
        playlist.items.select_related("file")
        .prefetch_related("visuals__file")
        .order_by("position", "pk")
    )
    if not rows:
        return [
            {
                "file": file,
                "images": [],
                "position": position,
            }
            # Keep the same default File ordering used by Player delivery for
            # a legacy playlist. UUID sorting would silently reorder playback
            # when the first structured item is added.
            for position, file in enumerate(playlist.files.all())
        ]
    return [
        {
            "file": item.file,
            "position": item.position,
            "images": [
                visual.file
                for visual in item.visuals.all().order_by("position", "pk")
            ],
        }
        for item in rows
    ]


def _set_admin_positions(
    playlist: Playlist,
    desired_items: Sequence[AdminPlaylistItem],
) -> None:
    """Persist sparse admin positions through a collision-free staging pass."""

    rows = list(playlist.items.select_for_update().order_by("position", "pk"))
    final_positions = [
        int(item.get("position", index))
        for index, item in enumerate(desired_items)
    ]
    if len(set(final_positions)) != len(final_positions):
        raise ValidationError("Позиции элементов плейлиста не должны повторяться.")
    if len(rows) != len(final_positions):
        raise ValidationError("Не удалось согласовать состав плейлиста.")
    if [row.position for row in rows] == final_positions:
        return

    occupied = {row.position for row in rows} | set(final_positions)
    temporary = []
    candidate = 0
    for _ in rows:
        while candidate in occupied:
            candidate += 1
        temporary.append(candidate)
        occupied.add(candidate)
        candidate += 1
    for row, position in zip(rows, temporary):
        row.position = position
    PlaylistItem.objects.bulk_update(rows, ("position",))
    for row, position in zip(rows, final_positions):
        row.position = position
    PlaylistItem.objects.bulk_update(rows, ("position",))


def validate_playlist_graph_change(
    playlist: Playlist,
    *,
    will_be_empty: bool = False,
) -> None:
    """Validate an admin graph edit before Django starts saving formsets."""

    ensure_structured_editable(playlist)
    if not will_be_empty:
        return

    from orders.models import AdOrder, BgOrder, Order

    filters = {"playlist": playlist, "is_active": True, "status__in": (0, 1)}
    if (
        Order.objects.filter(**filters).exists()
        or AdOrder.objects.filter(**filters).exists()
        or BgOrder.objects.filter(**filters).exists()
    ):
        raise ValidationError(
            "Сначала отмените активные заказы, затем можно очистить плейлист."
        )


@transaction.atomic
def sync_playlist_graph(
    playlist: Playlist,
    desired_items: Sequence[AdminPlaylistItem],
    *,
    previous_signature=None,
) -> bool:
    """Replace a playlist graph and refresh each active order exactly once."""

    playlist = Playlist.objects.select_for_update(no_key=True).get(pk=playlist.pk)
    current = playlist_graph_signature(playlist)
    before = current if previous_signature is None else previous_signature
    desired = resolved_graph_signature(desired_items)
    if current == desired:
        # Repair a stale legacy projection without producing a Player command.
        playlist.files.set(item["file"] for item in desired_items)
        if current[0] == "items":
            _set_admin_positions(playlist, desired_items)
    else:
        replace_playlist_items(playlist, desired_items)
        _set_admin_positions(playlist, desired_items)
    after = playlist_graph_signature(playlist)
    if before != after:
        try:
            refresh_playlist_orders(playlist)
        except ValidationError as exc:
            message = " ".join(exc.messages)
            raise AdminPlaylistDeliveryError(message) from exc
        except Exception as exc:
            logger.exception(
                "Playlist %s graph refresh failed; the admin transaction will roll back",
                playlist.pk,
            )
            raise AdminPlaylistDeliveryError(
                "Не удалось обновить доставку Player. Изменения плейлиста не сохранены."
            ) from exc
        return True
    return False


def next_copy_name(source_name: str) -> str:
    """Generate a unique copy name without exceeding the model limit."""

    number = 1
    while True:
        suffix = " (копия)" if number == 1 else f" (копия {number})"
        candidate = f"{source_name[: 255 - len(suffix)]}{suffix}"
        if not Playlist.objects.filter(name=candidate).exists():
            return candidate
        number += 1


@transaction.atomic
def copy_playlist(source: Playlist, *, owner) -> Playlist:
    """Clone content rows and visuals while sharing immutable media files."""

    source = (
        Playlist.objects.select_for_update(no_key=True)
        .prefetch_related("files", "items__file", "items__visuals__file")
        .get(pk=source.pk)
    )
    copy = Playlist.objects.create(
        name=next_copy_name(source.name),
        description=source.description,
        owner=owner,
    )
    source_items = list(source.items.all().order_by("position", "pk"))
    if not source_items:
        copy.files.set(source.files.all())
        return copy

    item_copies = [
        PlaylistItem(
            playlist=copy,
            file=item.file,
            position=item.position,
            weight=item.weight,
        )
        for item in source_items
    ]
    PlaylistItem.objects.bulk_create(item_copies)
    copied_by_source_id = {
        source_item.pk: copied_item
        for source_item, copied_item in zip(source_items, item_copies)
    }
    visuals = [
        PlaylistItemVisual(
            playlist_item=copied_by_source_id[item.pk],
            file=visual.file,
            position=visual.position,
            duration_seconds=visual.duration_seconds,
        )
        for item in source_items
        for visual in item.visuals.all().order_by("position", "pk")
    ]
    if visuals:
        PlaylistItemVisual.objects.bulk_create(visuals)
    copy.files.set(item.file for item in source_items)
    return copy


@transaction.atomic
def clear_playlists(playlists: Iterable[Playlist]) -> int:
    """Clear all selected playlists as one transaction."""

    identifiers = sorted(playlist.pk for playlist in playlists)
    locked = list(
        Playlist.objects.select_for_update(no_key=True)
        .filter(pk__in=identifiers)
        .order_by("pk")
    )
    removed = sum(len(snapshot_playlist_items(playlist)) for playlist in locked)
    for playlist in locked:
        sync_playlist_graph(playlist, [])
    return removed
