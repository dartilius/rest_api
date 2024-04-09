from rest_framework import serializers
from datetime import timedelta as td

from files.models import File, Playlist, PlaylistSettings, PlaylistFiles
from users.serializers import UserSerializer


class PlaylistSettingsSerializer(serializers.ModelSerializer):
    """Сериализация настроек плейлиста."""

    class Meta:
        fields = (
            'id',
            'playlist',
            'broadcast_type',
            'parameters'
        )
        model = PlaylistSettings


class ThemeSerializer(serializers.ModelSerializer):
    """Сериализация тематик файлов."""

    class Meta:
        fields = (
            'id',
            'name'
        )
        read_only_fields = ('id',)


class FileSerializer(serializers.ModelSerializer):
    """Сериализация файлов."""

    owner = UserSerializer(read_only=True)
    theme = ThemeSerializer(many=True)

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
            'theme',
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

    def create(self, validated_data):
        import hashlib
        import os

        file = validated_data.get('source')
        md5hash = hashlib.md5(file).hexdigest()
        sha256hash = hashlib.sha256(file).hexdigest()
        length = td(minutes=0, seconds=0)
        size = os.path.getsize(file)
        validated_data = dict(**validated_data, **{
            'size': size,
            'length': length,
            'md5hash': md5hash,
            'sha256hash': sha256hash
        })

        instance = File.objects.create(**validated_data)

        return instance


class PlaylistSerializer(serializers.ModelSerializer):
    """Сериализация плейлистов."""

    files = FileSerializer(many=True)
    settings = PlaylistSettingsSerializer()

    class Meta:
        fields = (
            'id',
            'name',
            'files',
            'description',
            'settings',
            'created'
        )
        read_only_fields = (
            'id',
            'created'
        )
        model = Playlist


class PlaylistFilesImagesField(serializers.ListField):
    """."""

    id = serializers.ListField()

    class Meta:
        model = HUY


class PlaylistFilesSerializer(serializers.ModelSerializer):
    """Сериализация связи плейлист - файл."""

    file = FileSerializer(many=True)
    playlist = PlaylistSerializer(required=True)
    images = PlaylistFilesImagesField()

    class Meta:
        model = PlaylistFiles
        fields = (
            'id',
            'file',
            'playlist',
            'images'
        )

