import base64

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import prefetch_related_objects
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from drf_spectacular.types import OpenApiTypes

from api.constants import Constants
from files.models import File, Playlist, PlaylistItem, Tag, TYPES
from files.playlist_api import (
    PlaylistContentSerializer,
    create_playlist_items,
    normalise_playlist_composition,
    playlist_api_composition,
)
from files.playlist_mutations import (
    refresh_playlist_orders,
    replace_playlist_items,
)


class Base64FileField(serializers.FileField):
    """Поле для получения и декодирования base64 строки в файл."""

    default_error_messages = {
        'invalid_file': 'Файл невозможно декодировать, либо он повреждён.',
        'invalid_format':
            'Файл должен быть закодирован в base64 строку.',
        'empty_name': 'Не указано имя либо расширение файла.',
        'empty_contents': 'Base64 строка ничего не содержит.',
        'empty': 'Отправлен пустой файл.'
    }
    empty_values = Constants.empty_values

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                if data in self.empty_values:
                    self.fail('empty')
                file_info, base64_str = data.split(';base64,')
                name, extension = file_info[5:].split('.')
                if name in self.empty_values or extension in self.empty_values:
                    self.fail('empty_name')
                if base64_str in self.empty_values:
                    self.fail('empty_contents')
                decoded_file = base64.b64decode(base64_str)
                complete_file_name = f'{name}.{extension}'
                data = ContentFile(decoded_file, name=complete_file_name)
            except (IndexError, TypeError, ValueError):
                self.fail('invalid_file')
            return super().to_internal_value(data)
        else:
            self.fail('invalid_format')


class TagSerializer(serializers.ModelSerializer):
    """Сериализация тегов файлов."""

    class Meta:
        fields = (
            'id',
            'name',
            'color'
        )
        read_only_fields = ('id',)
        model = Tag


class TagFileSerializer(serializers.Serializer):
    """Сериализация тегов в файле."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    color = serializers.CharField(max_length=7, required=False)


class FileSourceSerializer(serializers.ModelSerializer):
    """Сериализация одного файла."""

    source = serializers.FileField()

    class Meta:
        fields = (
            'id',
            'type',
            'source'
        )
        read_only_fields = (
            'id',
        )
        model = File


class FileSerializer(serializers.ModelSerializer):
    """Сериализация одного файла."""

    tags = TagFileSerializer(
        many=True,
        required=False,
        allow_empty=True,
        write_only=True,
    )
    source = Base64FileField(write_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'length',
            'size',
            'type',
            'source',
            'tags',
            'url'
        )
        read_only_fields = (
            'id',
            'length',
            'size',
            'url'
        )
        model = File

    # DRF-SPECTACULAR: help to resolve the returned type for OpenAPI generation
    @extend_schema_field(OpenApiTypes.STR)
    def get_url(self, instance) -> str:
        return instance.url

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['name'] = value.name
        repr_['owner'] = value.owner.full_name
        repr_['hash'] = value.hash
        repr_['type'] = TYPES[value.type]
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        return repr_

    def create(self, validated_data):
        try:
            tags = validated_data.pop('tags')
            tag_ids = [
                Tag.objects.get_or_create(
                    name=tag['name'],
                    defaults={'color': tag['color']} if 'color' in tag else {}
                )[0] for tag in tags
            ]
            instance = File.objects.create(**validated_data)
            instance.tags.set(tag_ids)
        except KeyError:
            instance = File.objects.create(**validated_data)
        return instance


class FileListSerializer(serializers.ModelSerializer):
    """Сериализация списка файлов."""

    class Meta:
        fields = (
            'id',
            'name',
            'length',
            'size',
            'type'
        )
        read_only_fields = fields
        model = File

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['type'] = TYPES[value.type]
        repr_['tags'] = [
            tag.name for tag in value.tags.all()
        ] if value.tags.exists() else None
        return repr_


def playlist_composition_signature(playlist):
    rows = list(PlaylistItem.objects.filter(playlist=playlist).order_by("position", "pk").values_list("pk", "file_id"))
    if not rows:
        return ("files", tuple(sorted(str(pk) for pk in playlist.files.values_list("pk", flat=True))))
    # Значимы только файлы и порядок. Сопровождение хранится в заказе.
    return ("items", tuple(str(file_id) for _, file_id in rows))


class PlaylistOwnerSerializer(serializers.Serializer):
    """Автор плейлиста: UUID пользователя и отображаемое ФИО."""

    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)


@extend_schema_serializer(exclude_fields=("items",))
class PlaylistSerializer(serializers.ModelSerializer):
    """Сериализация одного плейлиста."""

    owner = PlaylistOwnerSerializer(read_only=True, allow_null=True)

    items = PlaylistContentSerializer(
        many=True,
        required=False,
        write_only=True,
        max_length=1000,
    )
    files = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
        max_length=1000,
    )
    def to_internal_value(self, data):
        if isinstance(data, dict) and "audio_images" in data:
            raise serializers.ValidationError({
                "audio_images": "Картинки рекламного аудио настраиваются в едином заказе эфира."
            })
        return super().to_internal_value(data)

    class Meta:
        fields = (
            'id',
            'name',
            'description',
            'owner',
            'files',
            'items',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'created'
        )
        model = Playlist

    def validate(self, data):
        """Преобразуем ввод в список основных файлов без сопровождения."""
        composition_input = {key: data[key] for key in ("files", "items") if key in data}
        composition = normalise_playlist_composition(
            data,
            playlist=self.instance,
        )
        if composition is not None:
            data["_playlist_composition"] = composition
            if self.instance is not None:
                data["_playlist_input"] = composition_input
        return data

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("_playlist_composition")
        playlist = super().create(validated_data)
        create_playlist_items(playlist, items)
        prefetch_related_objects([playlist], "files", "items__file")
        return playlist

    @transaction.atomic
    def update(self, instance, validated_data):
        # Права уже проверены; no_key не мешает созданию связанных заказов.
        instance = Playlist.objects.select_for_update(no_key=True).get(pk=instance.pk)
        composition = validated_data.pop("_playlist_composition", None)
        composition_input = validated_data.pop("_playlist_input", None)
        if composition_input is not None:
            # Повторно проверяем состав после блокировки строки плейлиста.
            composition = normalise_playlist_composition(composition_input, playlist=instance)
        before = (
            playlist_composition_signature(instance)
            if composition is not None
            else None
        )
        try:
            instance = super().update(instance, validated_data)
            if composition is not None:
                replace_playlist_items(instance, composition)
            if before is not None and before != playlist_composition_signature(instance):
                refresh_playlist_orders(instance)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"files": exc.messages}) from exc
        return (
            Playlist.objects.select_related("owner")
            .prefetch_related("files", "items__file")
            .get(pk=instance.pk)
        )

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_.update(playlist_api_composition(value))
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        return repr_


class PlaylistListSerializer(serializers.ModelSerializer):
    """Сериализация списка плейлистов."""

    owner = PlaylistOwnerSerializer(read_only=True, allow_null=True)
    files_count = serializers.IntegerField(read_only=True)

    class Meta:
        fields = (
            'id',
            'name',
            'owner',
            'files_count',
            'created'
        )
        read_only_fields = fields
        model = Playlist

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['files_count'] = value.files.count()
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        return repr_


class PlaylistFileReferenceSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    url = serializers.URLField(read_only=True)


class PlaylistReadSerializer(serializers.ModelSerializer):
    """Describe the response independently of the UUID-based write format."""

    owner = PlaylistOwnerSerializer(read_only=True, allow_null=True)
    files = PlaylistFileReferenceSerializer(many=True, read_only=True)
    created = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Playlist
        fields = (
            "id",
            "name",
            "description",
            "owner",
            "files",
            "created",
        )
        read_only_fields = fields

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation.update(playlist_api_composition(value))
        return representation


class TagsFileSerializer(serializers.Serializer):
    """Схема добавления и удаления тэгов файла."""

    tags = serializers.ListField(child=serializers.CharField(max_length=255))
