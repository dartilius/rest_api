from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from files.filters import FileFilter, PlaylistFilter
from files.serializers import (
    PlaylistSerializer,
    PlaylistListSerializer,
    FileSerializer,
    FileListSerializer,
    TagSerializer
)
from files.models import Playlist, File, Tag
from users.permissions import AuthAndOnlySuperUserDelete


class TagViewSet(viewsets.ModelViewSet):
    """Работа с темами файлов."""

    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer


class FileViewSet(viewsets.ModelViewSet):
    """Работа с файлами."""

    queryset = File.objects.all().select_related(
        'owner'
    ).prefetch_related('tags').order_by('-created')
    serializer_class = FileSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FileFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = FileListSerializer
        else:
            serializer = FileSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PlaylistViewSet(viewsets.ModelViewSet):
    """Работа с плейлистами."""

    queryset = Playlist.objects.all().select_related(
        'owner'
    ).prefetch_related('files').order_by('-created')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = PlaylistFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = PlaylistListSerializer
        else:
            serializer = PlaylistSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

