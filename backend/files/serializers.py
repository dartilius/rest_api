from rest_framework import serializers

from files.models import File, Playlist, Tag
from users.serializers import CustomUserSerializer


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
    """Сериализация файлов."""

    tags = serializers.SlugRelatedField(
        slug_field='slug',
        many=True,
        queryset=Tag.objects.all(),
        write_only=True
    )

    class Meta:
        fields = (
            'id',
            'owner',
            'name',
            'hash',
            'length',
            'size',
            'file_type',
            'tags',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'hash',
            'length',
            'size',
            'created'
        )
        model = File

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['owner'] = (
            f'{value.owner.last_name} {value.owner.first_name}'
        )
        representation['hash'] = {
            'md5': value.md5hash,
            'sha256': value.sha256,
            'concat_hash': f'{value.md5hash}{value.sha256}'
        }
        representation['tags'] = [
            tag.name for tag in value.tags.all()
        ] if value.tags.exists() else None
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class FileListSerializer(serializers.ModelSerializer):
    """Сериализация файлов."""

    class Meta:
        fields = (
            'id',
            'name',
            'length',
            'size',
            'file_type',
            'created'
        )
        read_only_fields = fields
        model = File

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['owner'] = (
            f'{value.owner.last_name} {value.owner.first_name}'
        )
        representation['tags'] = [
            tag.name for tag in value.tags.all()
        ] if value.tags.exists() else None
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class PlaylistSerializer(serializers.ModelSerializer):
    """Сериализация плейлистов."""

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
    """Сериализация плейлистов."""

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
