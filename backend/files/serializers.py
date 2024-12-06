import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from api.constants import Constants
from files.models import File, Playlist, Tag, TYPES


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
            'name'
        )
        read_only_fields = ('id',)
        model = Tag


class TagFileSerializer(serializers.Serializer):
    """Сериализация тегов в файле."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)


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

    tags = TagFileSerializer(many=True, required=False, allow_empty=True)
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

    def get_url(self, instance):
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
            tag_ids = [Tag.objects.get_or_create(**tag)[0] for tag in tags]
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


class PlaylistSerializer(serializers.ModelSerializer):
    """Сериализация одного плейлиста."""

    files = serializers.SlugRelatedField(
        slug_field='id',
        queryset=File.objects.all(),
        write_only=True,
        many=True
    )

    class Meta:
        fields = (
            'id',
            'name',
            'description',
            'owner',
            'files',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'created'
        )
        model = Playlist

    def validate(self, data):
        """Проверяем, что все файлы в плейлисте одного типа."""
        if 'files' in self.initial_data:
            files_ids: list = self.initial_data.get('files')
            files = File.objects.filter(id__in=files_ids)
            playlist_files_types = {TYPES[file.type] for file in files}
            if len(playlist_files_types) > 1:
                raise serializers.ValidationError(
                    'Плейлист не должен содержать файлы разных типов: '
                    f'{playlist_files_types}'
                )
        return data

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['owner'] = value.owner.full_name
        repr_['files_count'] = value.files.count()
        repr_['files'] = [
            {'id': file.id,
             'name': file.name,
             'url': file.url} for file in value.files.all()
        ]
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        return repr_


class PlaylistListSerializer(serializers.ModelSerializer):
    """Сериализация списка плейлистов."""

    class Meta:
        fields = (
            'id',
            'name',
            'created'
        )
        read_only_fields = fields
        model = Playlist

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['owner'] = value.owner.full_name
        repr_['files_count'] = value.files.count()
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        return repr_
