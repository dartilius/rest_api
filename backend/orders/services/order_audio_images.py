"""Привязки картинок к аудио принадлежат рекламному заказу."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import Func, JSONField

from files.models import File, Playlist
from files.playlist_content import is_audio_file
from orders.models import Order


AUDIO_IMAGES_PARAMETER = "audio_images"
MAX_AUDIO_PARENTS = 1000
MAX_IMAGE_REFERENCES = 10000


class _AudioImageValues(Func):
    """Получаем UUID картинок из настроек заказа в PostgreSQL."""

    function = "jsonb_path_query_array"
    template = "%(function)s(%(expressions)s, '$.audio_images.*[*]'::jsonpath)"
    output_field = JSONField()


def _uuid_string(value, *, label: str) -> str:
    if not isinstance(value, str):
        raise ValidationError({"audio_images": f"{label} должен быть UUID-строкой."})
    try:
        return str(UUID(value))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValidationError({"audio_images": f"{label} {value!r} не является UUID."}) from exc


def _primary_file_ids(playlist: Playlist) -> set[UUID]:
    """Получаем основные файлы плейлиста не более чем двумя запросами."""
    item_ids = set(playlist.items.values_list("file_id", flat=True))
    if item_ids:
        return item_ids
    return set(playlist.files.values_list("pk", flat=True))


def _validate_and_resolve(
    value,
    *,
    playlist: Playlist,
    placement: str,
    allow_inactive_parents: bool,
    allow_inactive_images: bool,
    allow_duplicate_images: bool,
) -> tuple[dict[str, list[str]], dict[UUID, File]]:
    if placement != "advertising":
        raise ValidationError({
            "audio_images": "Картинки к аудио можно задавать только рекламному заказу."
        })
    if type(value) is not dict:
        raise ValidationError({
            "audio_images": "audio_images должен быть JSON-объектом: UUID аудио -> список UUID картинок."
        })
    if len(value) > MAX_AUDIO_PARENTS:
        raise ValidationError({
            "audio_images": f"В audio_images можно указать не более {MAX_AUDIO_PARENTS} аудиофайлов."
        })

    normalized: dict[str, list[str]] = {}
    referenced_ids: set[UUID] = set()
    image_references = 0
    for raw_parent, raw_images in value.items():
        parent = _uuid_string(raw_parent, label="Ключ")
        if parent in normalized:
            raise ValidationError({"audio_images": "The same audio file was supplied under equivalent UUID keys."})
        if not isinstance(raw_images, list):
            raise ValidationError({
                "audio_images": f"Значение для аудиофайла {parent} должно быть JSON-массивом UUID картинок."
            })
        image_references += len(raw_images)
        if image_references > MAX_IMAGE_REFERENCES:
            raise ValidationError({
                "audio_images": f"В одном заказе допускается не более {MAX_IMAGE_REFERENCES} ссылок на картинки."
            })

        images = [
            _uuid_string(raw_image, label="Картинка")
            for raw_image in raw_images
        ]
        if not allow_duplicate_images and len(set(images)) != len(images):
            raise ValidationError({
                "audio_images": f"Картинки для аудиофайла {parent} не должны повторяться."
            })
        normalized[parent] = images
        referenced_ids.add(UUID(parent))
        referenced_ids.update(UUID(image) for image in images)

    primary_ids = _primary_file_ids(playlist)
    parent_ids = {UUID(parent) for parent in normalized}
    unknown_parents = parent_ids - primary_ids
    if unknown_parents:
        raise ValidationError({
            "audio_images": (
                "Каждый ключ audio_images должен ссылаться на основной файл выбранного плейлиста. "
                f"Не найдены в плейлисте: {', '.join(sorted(map(str, unknown_parents)))}."
            )
        })

    file_queryset = File.objects.filter(pk__in=referenced_ids).only(
        "id", "type", "source", "is_active"
    ).order_by("pk")
    # Файлы блокируем только внутри транзакции: это защищает привязки
    # от удаления между проверкой и подготовкой команды для Player.
    if connection.in_atomic_block:
        file_queryset = file_queryset.select_for_update()
    files = file_queryset.in_bulk()
    missing = referenced_ids - set(files)
    if missing:
        raise ValidationError({
            "audio_images": f"Некоторые файлы не существуют: {', '.join(sorted(map(str, missing)))}."
        })

    for parent_id in parent_ids:
        parent = files[parent_id]
        if not allow_inactive_parents and not parent.is_active:
            raise ValidationError({
                "audio_images": f"Основной аудиофайл {parent_id} неактивен."
            })
        if not is_audio_file(parent):
            raise ValidationError({
                "audio_images": f"Основной файл {parent_id} не является аудиофайлом."
            })

    for images in normalized.values():
        for image_id in images:
            image = files[UUID(image_id)]
            if image.type != 2:
                raise ValidationError({
                    "audio_images": f"Файл {image_id} не является картинкой."
                })
            if not allow_inactive_images and not image.is_active:
                raise ValidationError({
                    "audio_images": f"Картинка {image_id} неактивна."
                })
    return normalized, files


def validate_order_audio_images(
    value,
    *,
    playlist: Playlist,
    placement: str,
    allow_inactive_images: bool = False,
    allow_inactive_parents: bool = False,
    allow_duplicate_images: bool = False,
) -> dict[str, list[str]]:
    """Проверяем привязки и приводим UUID к единому строковому виду."""
    normalized, _ = _validate_and_resolve(
        value,
        playlist=playlist,
        placement=placement,
        allow_inactive_parents=allow_inactive_parents,
        allow_inactive_images=allow_inactive_images,
        allow_duplicate_images=allow_duplicate_images,
    )
    return normalized


def get_order_audio_images(order: Order) -> dict[str, list[str]]:
    """Возвращаем отдельную копию привязок конкретного заказа."""
    value = (order.parameters or {}).get(AUDIO_IMAGES_PARAMETER, {})
    if type(value) is not dict:
        return {}
    return {
        str(parent): list(images) if isinstance(images, list) else []
        for parent, images in value.items()
    }


def with_order_audio_images(parameters, mapping: dict[str, list[str]]) -> dict:
    """Копируем параметры и заменяем привязки картинок заказа."""
    result = dict(parameters or {})
    if not mapping:
        result.pop(AUDIO_IMAGES_PARAMETER, None)
        return result
    result[AUDIO_IMAGES_PARAMETER] = {
        parent: list(images) for parent, images in mapping.items()
    }
    return result


def public_order_parameters(parameters) -> dict:
    """Исключаем приватную карту из общих параметров API и Player."""
    result = dict(parameters or {})
    result.pop(AUDIO_IMAGES_PARAMETER, None)
    return result


def active_order_image_usage(file_ids: Iterable[UUID | str]) -> set[UUID]:
    """Находим картинки, используемые действующими заказами.

    PostgreSQL выполняет один параметризованный запрос к JSON-картам.
    Для изолированных тестов на SQLite предусмотрено чтение обычного JSON.
    """

    requested: set[UUID] = set()
    for file_id in file_ids:
        try:
            requested.add(UUID(str(file_id)))
        except (AttributeError, TypeError, ValueError):
            continue
    if not requested:
        return set()

    requested_strings = {str(file_id) for file_id in requested}
    queryset = Order.objects.filter(is_active=True)
    if connection.vendor == "postgresql":
        values = queryset.annotate(
            _audio_image_values=_AudioImageValues("parameters"),
        ).filter(
            _audio_image_values__has_any_keys=list(requested_strings),
        ).values_list("_audio_image_values", flat=True)
    else:
        values = queryset.values_list("parameters", flat=True)

    used: set[UUID] = set()
    for value in values:
        if connection.vendor != "postgresql":
            if not isinstance(value, dict):
                continue
            mapping = value.get(AUDIO_IMAGES_PARAMETER, {})
            value = [
                image
                for images in mapping.values()
                if isinstance(images, list)
                for image in images
            ] if isinstance(mapping, dict) else []
        if not isinstance(value, list):
            continue
        for raw_id in value:
            try:
                file_id = UUID(str(raw_id))
            except (AttributeError, TypeError, ValueError):
                continue
            if file_id in requested:
                used.add(file_id)
    return used


def resolve_order_audio_image_files(order: Order) -> tuple[dict[str, list[str]], list[File]]:
    """Получаем файлы сохранённого сопровождения, не изменяя настройки заказа."""
    mapping = get_order_audio_images(order)
    if not mapping:
        return {}, []
    normalized, files = _validate_and_resolve(
        mapping,
        playlist=order.playlist,
        placement=order.placement,
        allow_inactive_parents=True,
        allow_inactive_images=True,
        allow_duplicate_images=True,
    )
    return normalized, [
        files[UUID(image_id)]
        for images in normalized.values()
        for image_id in images
    ]


def prune_order_audio_images_for_playlist(
    playlist: Playlist,
    *,
    remaining_primary_ids: Iterable[UUID | str],
) -> list[Order]:
    """Убираем ссылки на удалённые основные файлы; вызывающий код обновит версии заказов."""
    remaining = {str(UUID(str(identifier))) for identifier in remaining_primary_ids}
    changed: list[Order] = []
    orders = (
        Order.objects.select_for_update()
        .filter(playlist=playlist)
        .only("id", "parameters")
        .order_by("pk")
    )
    for order in orders:
        parameters = order.parameters or {}
        if AUDIO_IMAGES_PARAMETER not in parameters:
            continue
        current = parameters.get(AUDIO_IMAGES_PARAMETER)
        if type(current) is not dict:
            pruned = {}
        else:
            pruned = {
                str(parent): list(images) if isinstance(images, list) else []
                for parent, images in current.items()
                if str(parent) in remaining
            }
        if current == pruned:
            continue
        order.parameters = with_order_audio_images(parameters, pruned)
        changed.append(order)
    if changed:
        Order.objects.bulk_update(changed, ("parameters",), batch_size=500)
    return changed
