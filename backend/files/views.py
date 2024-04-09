from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from files.serializers import (
    PlaylistSerializer,
    PlaylistFilesSerializer,
    PlaylistSettingsSerializer,
    FileSerializer
)
from files.models import File, Playlist, PlaylistFiles, PlaylistSettings
from users.permissions import AuthAndOnlySuperUserDelete


class FileViewSet(viewsets.ModelViewSet):
    """Работа с файлами."""

    queryset = File.objects.all().select_related('owner')
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
        playlist.files.add(file)
        playlist.save()


class PlaylistViewSet(viewsets.ModelViewSet):
    """Работа с плейлистами."""

    serializer_class = PlaylistSerializer
    queryset = Playlist.objects.all().select_related(
        'owner', 'settings'
    ).prefetch_related('files')
    pagination_class = LimitOffsetPagination
    # permission_classes = [AuthAndOnlySuperUserDelete, ]


class PlaylistSettingsViewSet(viewsets.ModelViewSet):
    """Работа с настройками номенклатуры."""

    serializer_class = PlaylistSettingsSerializer
    queryset = Playlist.objects.select_related('playlist')

    def get_queryset(self):
        playlist_id = self.kwargs.get('playlist_id')
        return get_object_or_404(
            Playlist.objects.prefetch_related('settings'),
            id=playlist_id
        ).settings


class PlaylistFilesViewSet(viewsets.ModelViewSet):
    """Работа с файлами плейлиста."""

    serializer_class = PlaylistFilesSerializer
    queryset = PlaylistFiles.objects.filter()
