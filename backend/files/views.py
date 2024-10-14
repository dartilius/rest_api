from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from ch_statistic.models import (
    ADStat,
    MusicStat,
    ImageStat,
    VideoStat,
    TickerStat
)
from ch_statistic.serializers import (
    FileAdStatSerializer,
    FileMusicStatSerializer,
    FileImageStatSerializer,
    FileVideoStatSerializer,
    FileTickerStatSerializer
)

from files.filters import FileFilter, PlaylistFilter
from files.serializers import (
    PlaylistSerializer,
    PlaylistListSerializer,
    FileSerializer,
    FileListSerializer,
    TagSerializer, FileSourceSerializer
)
from files.models import Playlist, File, Tag


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

    # @action(detail=False, methods=['POST'])
    # def download(self, request):
    #     from api.constants import Constants
    #     from datetime import timedelta as td
    #
    #     client = Constants.get_minio_client()
    #     file_ids = request.data['file_id']
    #     file_urls = []
    #     for file_id in file_ids:
    #         file = File.objects.get(pk=file_id)
    #         url = client.get_presigned_url(
    #             'GET',
    #             'local-media',
    #             f'{file.source}',
    #             expires=td(hours=2)
    #         )
    #         file_urls.append(url)
    #     return Response(file_urls)

    @action(detail=True, methods=['GET'], url_path='stat')
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
                statistics = ADStat.objects.filter(file=pk)
                data = FileAdStatSerializer(statistics, many=True).data
            case 1:
                statistics = MusicStat.objects.filter(file=pk)
                data = FileMusicStatSerializer(statistics, many=True).data
            case 2:
                statistics = ImageStat.objects.filter(file=pk)
                data = FileImageStatSerializer(statistics, many=True).data
            case 3:
                statistics_bg = VideoStat.objects.filter(file=pk)
                statistics_ad = ADStat.objects.filter(file=pk)
                data_bg = FileVideoStatSerializer(statistics_bg,
                                                  many=True).data
                data_ad = FileAdStatSerializer(statistics_ad, many=True).data
                data = data_ad + data_bg
            case 4:
                statistics = TickerStat.objects.filter(file=pk)
                data = FileTickerStatSerializer(statistics, file=True).data
            case _:
                data = []

        return Response(data, status=HTTP_200_OK)


class PlaylistViewSet(viewsets.ModelViewSet):
    """Работа с плейлистами."""

    queryset = Playlist.objects.all().select_related(
        'owner'
    ).prefetch_related('files')
    filter_backends = [DjangoFilterBackend]
    filterset_class = PlaylistFilter

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


class UploadFilesViewSet(viewsets.ModelViewSet):
    """Для загрузки файлов из старой админки."""

    queryset = File.objects.all().select_related(
        'owner'
    )
    serializer_class = FileSourceSerializer()

    def get_serializer(self, *args, **kwargs):
        serializer = FileSourceSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
