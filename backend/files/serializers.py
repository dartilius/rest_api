from rest_framework import serializers

from files.models import File, Playlist, PlaylistFiles, Tag
from users.serializers import UserSerializer


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

    owner = UserSerializer(read_only=True)
    tag = TagSerializer(many=True, required=False)

    class Meta:
        fields = (
            'id',
            'owner',
            'name',
            'source',
            'md5hash',
            'sha256hash',
            'hash',
            'length',
            'size',
            'file_type',
            'tag',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'md5hash',
            'sha256hash',
            'hash',
            'length',
            'size',
            'created'
        )
        model = File


class PlaylistSerializer(serializers.ModelSerializer):
    """Сериализация плейлистов."""

    files = FileSerializer(many=True)

    class Meta:
        fields = (
            'id',
            'name',
            'files',
            'description',
            'created'
        )
        read_only_fields = (
            'id',
            'created'
        )
        model = Playlist


class PlaylistFilesSerializer(serializers.ModelSerializer):
    """Сериализация связи плейлист - файл."""

    file = FileSerializer(many=True)
    playlist = PlaylistSerializer(required=True)
    # images = PlaylistFilesImagesField()

    class Meta:
        model = PlaylistFiles
        fields = (
            'id',
            'file',
            'playlist',
            'images'
        )

