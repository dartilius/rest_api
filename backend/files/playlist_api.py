"""API плейлистов: основные файлы и порядок воспроизведения."""

from pathlib import PurePosixPath
from collections.abc import Mapping
from rest_framework import serializers

from files.models import File, Playlist, PlaylistItem, TYPES
from files.playlist_content import is_audio_file


class PlaylistFilesChangeSerializer(serializers.Serializer):
    """Формат добавления и удаления основных файлов."""

    files = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="**files** — UUID основных файлов.",
    )


class PlaylistContentSerializer(serializers.Serializer):
    """Совместимый экспериментальный ввод файлов; основное поле API — files."""

    file = serializers.UUIDField(
        help_text="**file** — UUID основного файла."
    )
    def to_internal_value(self, data):
        # Не игнорируем устаревший параметр молча: настройка теперь в заказе.
        if isinstance(data, Mapping) and "images" in data:
            raise serializers.ValidationError({
                "images": "Картинки рекламного аудио настраиваются в едином заказе эфира."
            })
        return super().to_internal_value(data)

    def validate(self, attrs):
        # При PATCH вложенный сериализатор тоже пропускает обязательные поля.
        if "file" not in attrs:
            raise serializers.ValidationError(
                {"file": "Укажите UUID основного файла."}
            )
        return attrs


def normalise_playlist_composition(attrs, *, playlist: Playlist | None):
    """Проверяем только основные файлы; сопровождение принадлежит заказу."""
    has_items = "items" in attrs
    has_files = "files" in attrs
    if "audio_images" in attrs:
        raise serializers.ValidationError({
            "audio_images": "Картинки рекламного аудио настраиваются в едином заказе эфира."
        })
    if has_items and has_files:
        raise serializers.ValidationError("Передайте files без дополнительной обёртки items.")
    if not has_items and not has_files:
        if playlist is None:
            raise serializers.ValidationError({"files": "Укажите упорядоченный список UUID файлов."})
        return None
    # Старый экспериментальный ввод принимаем только для файлов, без картинок.
    # В документации и ответах используется обычный массив files.
    raw_files = attrs.pop("items") if has_items else [
        {"file": identifier} for identifier in attrs.pop("files")
    ]
    try:
        return resolve_playlist_items(raw_files, allow_empty=playlist is not None)
    except serializers.ValidationError as exc:
        raise serializers.ValidationError({"files": exc.detail}) from exc


def resolve_playlist_items(playlist_files, *, allow_empty=False):
    """Разрешаем UUID файлов одним запросом, сохраняя переданный порядок."""
    if (not playlist_files and not allow_empty) or len(playlist_files) > 1000:
        raise serializers.ValidationError("Укажите от 1 до 1000 основных файлов.")
    if any("images" in entry for entry in playlist_files):
        raise serializers.ValidationError("Картинки рекламного аудио настраиваются в едином заказе эфира.")
    identifiers = [entry["file"] for entry in playlist_files]
    if len(set(identifiers)) != len(identifiers):
        raise serializers.ValidationError("Основной файл не должен повторяться в плейлисте.")
    files = File.objects.filter(pk__in=identifiers).in_bulk()
    if set(files) != set(identifiers):
        raise serializers.ValidationError("Некоторые файлы не существуют.")
    if any(not file.is_active for file in files.values()):
        raise serializers.ValidationError("Основной файл не существует или неактивен.")
    return [{"file": files[identifier]} for identifier in identifiers]


def create_playlist_items(playlist, playlist_files):
    """Храним позицию каждого файла. Картинки к аудио здесь не создаём."""
    PlaylistItem.objects.bulk_create([
        PlaylistItem(playlist=playlist, file=entry["file"], position=position)
        for position, entry in enumerate(playlist_files)
    ])
    playlist.files.set(entry["file"] for entry in playlist_files)

def _file_reference(file):
    media_type = TYPES[file.type]
    if is_audio_file(file):
        media_type = "audio"
    elif file.type == 4:
        suffix = PurePosixPath(file.source.name or "").suffix.lower()
        if suffix in {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm", ".mpeg", ".mpg", ".m4v", ".flv", ".ts"}:
            media_type = "video"
        elif suffix in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}:
            media_type = "image"
    return {
        "id": str(file.pk),
        "name": file.name,
        "type": media_type,
        "url": file.url,
    }


def playlist_api_composition(playlist):
    """Возвращаем только основные файлы в порядке воспроизведения."""

    items = list(playlist.items.all())
    if not items:
        return {
            "files": [
                _file_reference(file) for file in playlist.files.all()
            ],
        }
    return {
        "files": [_file_reference(item.file) for item in items],
    }
