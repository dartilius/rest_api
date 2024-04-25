from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from files.serializers import (
    PlaylistSerializer,
    PlaylistFilesSerializer,
    FileSerializer, TagSerializer
)
from files.models import File, Playlist, PlaylistFiles, Tag
from users.permissions import AuthAndOnlySuperUserDelete


class TagViewSet(viewsets.ModelViewSet):
    """Работа с темами файлов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = LimitOffsetPagination


class FileViewSet(viewsets.ModelViewSet):
    """Работа с файлами."""

    queryset = File.objects.all().select_related(
        'owner'
    ).prefetch_related('theme')
    serializer_class = FileSerializer
    pagination_class = LimitOffsetPagination
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        file = serializer.save(owner=self.request.user)
        playlist = Playlist.objects.create(
            owner=self.request.user,
            name=file.name,
            description=file.name
        )
        playlist_files = PlaylistFiles.objects.create(
            playlist=playlist,
            file=file
        )


class PlaylistViewSet(viewsets.ModelViewSet):
    """Работа с плейлистами."""

    serializer_class = PlaylistSerializer
    queryset = Playlist.objects.all().select_related(
        'owner', 'settings'
    ).prefetch_related('files')
    pagination_class = LimitOffsetPagination
    # permission_classes = [AuthAndOnlySuperUserDelete, ]


class PlaylistFilesViewSet(viewsets.ModelViewSet):
    """Работа с файлами плейлиста."""

    serializer_class = PlaylistFilesSerializer
    queryset = PlaylistFiles.objects.filter()
