import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from files.models import File, Playlist, Tag


class Base64FileField(serializers.FileField):
    """Кастомное поле для получения и декодирования base64 строки в файл."""

    empty_values = ([], {}, (), '', None)

    default_error_messages = {
        'invalid_file': 'Файл невозможно декодировать, либо он повреждён.',
        'invalid_format':
            'Не правильный формат. '
            'Файл должен быть закодирован в base64 строку.',
        'no_name': 'Имя файла невозможно извлечь из отправленных данных.',
        'empty': 'Отправленный файл пуст.',
    }

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                file_info, base64_str = data.split(';base64,')
                name, extension = file_info[5:].split('.')
                if name in self.empty_values:
                    self.fail('no_name')
                if base64_str in self.empty_values:
                    self.fail('empty')
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


class FileSerializer(serializers.ModelSerializer):
    """Сериализация одного файла."""

    tags = serializers.SlugRelatedField(
        slug_field='name',
        many=True,
        queryset=Tag.objects.all(),
        write_only=True
    )
    source = Base64FileField(write_only=True)

    class Meta:
        fields = (
            'id',
            'length',
            'size',
            'file_type',
            'source',
            'tags'
        )
        read_only_fields = (
            'id',
            'length',
            'size'
        )
        model = File

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['name'] = value.name
        representation['owner'] = (
            f'{value.owner.last_name} {value.owner.first_name}'
        )
        representation['hash'] = {
            'md5': value.md5hash,
            'sha256': value.sha256hash,
            'concat_hash': value.hash
        }
        representation['tags'] = [
            tag.name for tag in value.tags.all()
        ] if value.tags.exists() else None
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class FileListSerializer(serializers.ModelSerializer):
    """Сериализация списка файлов."""

    class Meta:
        fields = (
            'id',
            'name',
            'length',
            'size',
            'file_type'
        )
        read_only_fields = fields
        model = File

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['tags'] = [
            tag.name for tag in value.tags.all()
        ] if value.tags.exists() else None
        return representation


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

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['owner'] = (
            f'{value.owner.last_name} {value.owner.first_name}'
        )
        representation['files'] = [
            {'id': file.id, 'name': file.name} for file in value.files.all()
        ]
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation


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
        representation = super().to_representation(value)
        representation['owner'] = (
            f'{value.owner.last_name} {value.owner.first_name}'
        )
        representation['files_count'] = len(value.files.all())
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation
