"""Атомарное редактирование состава плейлиста из админки."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from typing import TypedDict

from django.core.exceptions import ValidationError
from django.db import transaction

from files.models import File, Playlist, PlaylistItem
from files.playlist_mutations import (
    ensure_structured_editable,
    refresh_playlist_orders,
    replace_playlist_items,
)

logger = logging.getLogger(__name__)

HISTORICAL_VISUALS_ERROR = (
    "Нельзя удалить или заменить основной элемент с архивными картинками. "
    "Проверьте старые данные перед удалением. Новое сопровождение задаётся в заказе."
)


class AdminPlaylistDeliveryError(Exception):
    """A graph edit was rolled back because Player delivery could not refresh."""


class AdminPlaylistItem(TypedDict):
    """Один основной файл и его позиция в форме админки."""

    item_id: int | None
    file: File
    position: int


def playlist_graph_signature(playlist: Playlist):
    """Читаем порядок основных файлов без получения ссылок на контент."""

    items = list(
        PlaylistItem.objects.filter(playlist=playlist)
        .order_by("position", "pk")
        .values_list("pk", "file_id")
    )
    if not items:
        return (
            "files",
            tuple(
                sorted(str(pk) for pk in playlist.files.values_list("pk", flat=True))
            ),
        )

    return (
        "items",
        tuple(str(file_id) for _, file_id in items),
    )


def resolved_graph_signature(items: Sequence[AdminPlaylistItem]):
    return (
        "items",
        tuple(str(item["file"].pk) for item in items),
    )


def snapshot_playlist_items(playlist: Playlist) -> list[AdminPlaylistItem]:
    """Читаем позиции файлов; для старых плейлистов используем M2M-связь."""

    rows = list(playlist.items.select_related("file").order_by("position", "pk"))
    if not rows:
        return [
            {
                "item_id": None,
                "file": file,
                "position": position,
            }
            # Сохраняем прежний порядок старого плейлиста, затем добавляем
            # новые файлы в конец. Сортировка по UUID изменила бы эфир.
            for position, file in enumerate(playlist.files.all())
        ]
    return [
        {
            "item_id": item.pk,
            "file": item.file,
            "position": item.position,
        }
        for item in rows
    ]


def _set_admin_positions(
    playlist: Playlist,
    desired_items: Sequence[AdminPlaylistItem],
) -> None:
    """Сохраняем позиции через временную нумерацию без конфликтов уникальности."""

    rows = list(playlist.items.select_for_update().order_by("position", "pk"))
    final_positions = [
        int(item.get("position", index)) for index, item in enumerate(desired_items)
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


def validate_historical_playlist_items(
    playlist: Playlist,
    desired_items: Sequence[AdminPlaylistItem],
) -> None:
    """Сохраняем старые связи: разрешаем менять только порядок их основных файлов."""

    desired_by_id = {
        item["item_id"]: item for item in desired_items if item["item_id"] is not None
    }
    protected = (
        PlaylistItem.objects.filter(
            playlist=playlist,
            visuals__isnull=False,
        )
        .values_list("pk", "file_id")
        .distinct()
    )
    for item_id, file_id in protected:
        desired = desired_by_id.get(item_id)
        if desired is None or desired["file"].pk != file_id:
            raise ValidationError(HISTORICAL_VISUALS_ERROR)


def _retain_admin_item_identity(
    playlist: Playlist,
    desired_items: Sequence[AdminPlaylistItem],
) -> None:
    """Сохраняем идентификаторы строк при обновлении основных файлов."""

    existing = list(PlaylistItem.objects.select_for_update().filter(playlist=playlist))
    existing_by_id = {item.pk: item for item in existing}
    desired_ids = {
        item["item_id"] for item in desired_items if item["item_id"] is not None
    }
    if not desired_ids.issubset(existing_by_id):
        raise ValidationError(
            "Элемент плейлиста был изменён параллельно. Обновите страницу."
        )

    removed_ids = set(existing_by_id) - desired_ids
    if removed_ids:
        PlaylistItem.objects.filter(pk__in=removed_ids).delete()

    changed = []
    for item in desired_items:
        item_id = item["item_id"]
        if item_id is None:
            continue
        current = existing_by_id[item_id]
        if current.file_id != item["file"].pk:
            current.file = item["file"]
            changed.append(current)
    if changed:
        PlaylistItem.objects.bulk_update(changed, ("file",))


def validate_playlist_graph_change(
    playlist: Playlist,
    *,
    desired_items: Sequence[AdminPlaylistItem] | None = None,
    will_be_empty: bool = False,
) -> None:
    """Проверяем состав до сохранения форм админки."""

    ensure_structured_editable(playlist)
    if desired_items is not None:
        validate_historical_playlist_items(playlist, desired_items)
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
    """Обновляем состав и отправляем одну новую версию каждому действующему заказу."""

    playlist = Playlist.objects.select_for_update(no_key=True).get(pk=playlist.pk)
    # Блокируем строки на время проверки и записи нового состава.
    list(
        PlaylistItem.objects.select_for_update()
        .filter(playlist=playlist)
        .values_list("pk", flat=True)
    )
    current = playlist_graph_signature(playlist)
    before = current if previous_signature is None else previous_signature
    desired = resolved_graph_signature(desired_items)
    validate_historical_playlist_items(playlist, desired_items)
    if current == desired:
        # Исправляем M2M-проекцию и позиции без лишней повторной отправки.
        playlist.files.set(item["file"] for item in desired_items)
    else:
        validate_playlist_graph_change(
            playlist,
            desired_items=desired_items,
            will_be_empty=not desired_items,
        )
        _retain_admin_item_identity(playlist, desired_items)
        replace_playlist_items(playlist, [{"file": item["file"]} for item in desired_items])
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
    """Clone primary content rows while sharing immutable media files."""

    source = (
        Playlist.objects.select_for_update(no_key=True)
        .prefetch_related("files", "items__file")
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
