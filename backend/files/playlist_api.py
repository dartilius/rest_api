"""Ordered primary files and attached audio visuals in the existing REST API."""

from collections import Counter

from rest_framework import serializers

from files.models import File, Playlist, PlaylistItem, PlaylistItemVisual
from files.playlist_content import is_audio_file


class PlaylistFilesChangeSerializer(serializers.Serializer):
    """Schema of the existing add/remove primary-file operations."""

    files = serializers.ListField(child=serializers.UUIDField(), help_text=(
        "**files** — UUID основных файлов. Картинки, прикреплённые к аудио, "
        "изменяются через **items[].images**, а не этим методом."
    ))


class PlaylistImageDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    url = serializers.URLField(read_only=True)
    position = serializers.IntegerField(read_only=True)


class PlaylistContentSerializer(serializers.Serializer):
    file = serializers.UUIDField(help_text="**file** — UUID основного ролика. Обязательное поле; один основной файл не повторяется.")
    images = serializers.ListField(child=serializers.UUIDField(), required=False, default=list, max_length=1000,
        help_text="**images** — UUID картинок к этому аудио в порядке показа. Необязательно, по умолчанию []; только изображения. Время рассчитывает Player по длительности аудио.")
    position = serializers.IntegerField(read_only=True)
    file_name = serializers.CharField(read_only=True)
    file_url = serializers.URLField(read_only=True)
    image_files = PlaylistImageDetailSerializer(many=True, read_only=True)

    def validate(self, attrs):
        # Parent PATCH skips required/default fields even in nested serializers.
        # Each item is a complete composition row, not a partial child update.
        if "file" not in attrs:
            raise serializers.ValidationError({"file": "Укажите UUID основного файла."})
        return attrs

    def to_representation(self, item):
        visuals = list(item.visuals.all())
        return {"file": str(item.file_id), "images": [str(visual.file_id) for visual in visuals],
            "position": item.position, "file_name": item.file.name, "file_url": item.file.url,
            "image_files": [{"id": str(visual.file_id), "name": visual.file.name,
                "url": visual.file.url, "position": visual.position} for visual in visuals]}


def resolve_playlist_items(items, *, allow_empty=False, playlist: Playlist | None = None):
    if (not items and not allow_empty) or len(items) > 1000:
        raise serializers.ValidationError("Укажите от 1 до 1000 основных роликов.")
    primary_ids = [item["file"] for item in items]
    if len(set(primary_ids)) != len(primary_ids):
        raise serializers.ValidationError("Основной файл не должен повторяться в плейлисте.")
    identities = set(primary_ids)
    references = len(primary_ids)
    for item in items:
        identities.update(item.get("images", []))
        references += len(item.get("images", []))
    if references > 10000:
        raise serializers.ValidationError("Слишком много файлов и картинок в одном плейлисте.")
    files = {file.pk: file for file in File.objects.filter(pk__in=identities)}
    if set(files) != identities:
        raise serializers.ValidationError("Некоторые файлы не существуют.")
    retained_inactive = Counter()
    if playlist is not None:
        retained_inactive.update(
            PlaylistItemVisual.objects.filter(
                playlist_item__playlist=playlist,
                file__is_active=False,
            ).values_list("playlist_item__file_id", "file_id")
        )
    resolved = []
    for index, item in enumerate(items):
        primary = files[item["file"]]
        images = [files[identity] for identity in item.get("images", [])]
        if not primary.is_active:
            raise serializers.ValidationError(
                {index: {"file": "Основной файл не существует или неактивен."}}
            )
        for image in images:
            if image.is_active:
                continue
            retained_key = (primary.pk, image.pk)
            if retained_inactive[retained_key] <= 0:
                raise serializers.ValidationError(
                    {index: {"images": "Нельзя добавить новую неактивную картинку."}}
                )
            retained_inactive[retained_key] -= 1
        if images and not is_audio_file(primary):
            raise serializers.ValidationError({index: {"images": "Сопровождение можно прикрепить только к аудиофайлу."}})
        if any(image.type != 2 for image in images):
            raise serializers.ValidationError({index: {"images": "Сопровождение должно содержать только картинки."}})
        resolved.append({"file": primary, "images": images})
    return resolved


def create_playlist_items(playlist, items):
    """Caller owns the transaction; image files are never primary members."""
    for position, item in enumerate(items):
        primary = PlaylistItem.objects.create(playlist=playlist, file=item["file"], position=position)
        PlaylistItemVisual.objects.bulk_create([
            PlaylistItemVisual(playlist_item=primary, file=image, position=index)
            for index, image in enumerate(item["images"])
        ])
    playlist.files.set(item["file"] for item in items)
