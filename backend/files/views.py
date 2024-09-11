from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from ch_statistic.models import ADStat, MusicStat, ImageStat, VideoStat, TickerStat
from ch_statistic.serializers import AdStatSerializer, MusicStatSerializer, ImageStatSerializer, VideoStatSerializer, \
    TickerStatSerializer
# from rest_framework.permissions import IsAuthenticatedOrReadOnly

from files.filters import FileFilter, PlaylistFilter
from files.serializers import (
    PlaylistSerializer,
    PlaylistListSerializer,
    FileSerializer,
    FileListSerializer,
    TagSerializer
)
from files.models import Playlist, File, Tag
# from users.permissions import AuthAndOnlySuperUserDelete


class TagViewSet(viewsets.ModelViewSet):
    """Работа с темами файлов."""

    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer


class FileViewSet(viewsets.ModelViewSet):
    """Работа с файлами."""

    queryset = File.objects.all().select_related(
        'owner'
    )
    serializer_class = FileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = FileFilter
    parser_classes = [JSONParser]
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

    @action(
        detail=True,
        methods=['GET'],
        url_path='stat'
    )
    def get_stat(self, request, pk):
        """Отображение статистики музыки."""
        try:
            file = get_object_or_404(File, id=pk)
        except ValidationError:
            return Response(
                {'detail': f'Значение "{pk}" не является верным UUID-ом.'},
                status=HTTP_400_BAD_REQUEST
            )
        match file.file_type:
            case 0:
                statistics = ADStat.objects.filter(value=pk)
                data = AdStatSerializer(statistics, many=True).data
            case 1:
                statistics = MusicStat.objects.filter(value=pk)
                data = MusicStatSerializer(statistics, many=True).data
            case 2:
                statistics = ImageStat.objects.filter(value=pk)
                data = ImageStatSerializer(statistics, many=True).data
            case 3:
                statistics_bg = VideoStat.objects.filter(value=pk)
                statistics_ad = ADStat.objects.filter(value=pk)
                data_bg = VideoStatSerializer(statistics_bg, many=True).data
                data_ad = AdStatSerializer(statistics_ad, many=True).data
                data = data_ad + data_bg
            case 4:
                statistics = TickerStat.objects.filter(value=pk)
                data = TickerStatSerializer(statistics, many=True).data
            case _:
                data=[]

        return Response(data, status=HTTP_200_OK)

class PlaylistViewSet(viewsets.ModelViewSet):
    """Работа с плейлистами."""

    queryset = Playlist.objects.all().select_related(
        'owner'
    ).prefetch_related('files')
    filter_backends = [DjangoFilterBackend]
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
