from datetime import datetime as dt
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from ch_statistic.models import ADStat, MusicStat, VideoStat, ImageStat, TickerStat
from ch_statistic.serializers import AdStatSerializer, MusicStatSerializer, VideoStatSerializer, ImageStatSerializer, \
    TickerStatSerializer
from ch_statistic.tasks import create_statistic
from files.models import File
from nomenclatures.filters import NomenclatureFilter
from nomenclatures.serializers import (
    NomenclatureSerializer,
    NomenclatureListSerializer,
    NomenclatureGroupSerializer,
    NomenclatureGroupListSerializer,
    StatusHistorySerializer
)
from nomenclatures.models import (
    Nomenclature,
    NomenclatureGroup, NomenclatureAvailability
)
from tasks.models import Task
from users.permissions import AuthAndOnlySuperUserDelete


class NomenclatureViewSet(viewsets.ModelViewSet):
    """Работа с номенклатурами."""

    queryset = Nomenclature.objects.filter(
        is_active=True
    ).select_related('owner', 'availability')
    filter_backends = [DjangoFilterBackend]
    filterset_class = NomenclatureFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = NomenclatureListSerializer
        else:
            serializer = NomenclatureSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)

    def perform_create(self, serializer):
        nomenclatures = serializer.save(owner=self.request.user)
        if isinstance(nomenclatures, list):
            for nomenclature in nomenclatures:
                group = NomenclatureGroup.objects.create(
                    owner=self.request.user,
                    name=nomenclature.name,
                )
                group.clients.add(nomenclature)
                group.save()
        else:
            group = NomenclatureGroup.objects.create(
                owner=self.request.user,
                name=nomenclatures.name,
            )
            group.clients.add(nomenclatures)
            group.save()

    def perform_update(self, serializer):
        nomenclature = serializer.instance
        if (
            'name' in serializer.validated_data and
            serializer.validated_data['name'] != nomenclature.name
        ):
            group = NomenclatureGroup.objects.exclude(
                ~Q(clients=nomenclature.id)
            ).first()
            group.name = serializer.validated_data['name']
            group.save()
        serializer.save()

    def perform_destroy(self, instance):
        group = NomenclatureGroup.objects.exclude(
            ~Q(clients=instance.id)
        ).first()
        group.delete()
        instance.delete()

    @action(
        detail=True,
        methods=['GET'],
        url_path='status_history'
    )
    def get_status_history(self, request, pk):
        nomenclature = get_object_or_404(Nomenclature, id=pk)
        history = nomenclature.history.all()
        serializer = StatusHistorySerializer(history, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST'],
        url_path='pending_tasks'
    )
    def pending_tasks(self, request, pk):
        """Отдача задач для клиентов и обработка присылаемых данных."""
        nomenclature = get_object_or_404(Nomenclature, id=pk)
        nom_update = False
        if 'version' in request.data:
            nomenclature.version = request.data['version']
            nom_update = True

        if 'hw_info' in request.data:
            nomenclature.hw_info = request.data['hw_info']
            nom_update = True

        if nom_update:
            nomenclature.save()

        if 'statistic' in request.data:
            statistics = request.data['statistic']
            for stat_type, stat_list in statistics.items():
                create_statistic.delay(stat_type, nomenclature.id, stat_list)


        if 'task_status' in request.data:
            task_list = list()
            for task in request.data['task_status']:
                task_id, task_status = task.items()
                task_instance = Task.objects.get(id=task_id)
                task_instance.status = task_status
                task_list.append(task_instance)
            Task.objects.bulk_update(task_list, ['status'])

        NomenclatureAvailability.objects.update_or_create(
            client=nomenclature,
            defaults={'last_answer_date': dt.now()}
        )
        pending_tasks = Task.objects.filter(
            client=nomenclature.id,
            status=0
        )
        tasks = {'tasks': [
            {'task_id': task.id,
             'task_type': task.type,
             'parameters': task.parameters}
            for task in pending_tasks]}
        return Response(tasks, status=HTTP_200_OK)

    @action(
        detail=True,
        methods=['GET'],
        url_path='ad_stat'
    )
    def get_ad_stat(self, request, pk):
        """Отображение статистики рекламы конкретной номенклатуры."""
        try:
            nomenclature = get_object_or_404(Nomenclature, id=pk)
        except ValidationError:
            return Response(
                {'detail': f'Значение "{pk}" не является верным UUID-ом.'},
                status=HTTP_400_BAD_REQUEST
            )
        statistics = ADStat.objects.filter(client=pk)
        serializer = AdStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(
        detail=True,
        methods=['GET'],
        url_path='music_stat'
    )
    def get_music_stat(self, request, pk):
        """Отображение статистики музыки конкретной номенклатуры."""
        try:
            nomenclature = get_object_or_404(Nomenclature, id=pk)
        except ValidationError:
            return Response(
                {'detail': f'Значение "{pk}" не является верным UUID-ом.'},
                status=HTTP_400_BAD_REQUEST
            )
        statistics = MusicStat.objects.filter(client=pk)
        serializer = MusicStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(
        detail=True,
        methods=['GET'],
        url_path='video_stat'
    )
    def get_video_stat(self, request, pk):
        """Отображение статистики видео конкретной номенклатуры."""
        try:
            nomenclature = get_object_or_404(Nomenclature, id=pk)
        except ValidationError:
            return Response(
                {'detail': f'Значение "{pk}" не является верным UUID-ом.'},
                status=HTTP_400_BAD_REQUEST
            )
        statistics = VideoStat.objects.filter(client=pk)
        serializer = VideoStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(
        detail=True,
        methods=['GET'],
        url_path='image_stat'
    )
    def get_image_stat(self, request, pk):
        """Отображение статистики картинок конкретной номенклатуры."""
        try:
            nomenclature = get_object_or_404(Nomenclature, id=pk)
        except ValidationError:
            return Response(
                {'detail': f'Значение "{pk}" не является верным UUID-ом.'},
                status=HTTP_400_BAD_REQUEST
            )
        statistics = ImageStat.objects.filter(client=pk)
        serializer = ImageStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(
        detail=True,
        methods=['GET'],
        url_path='ticker_stat'
    )
    def get_ticker_stat(self, request, pk):
        """Отображение статистики бегущих строк конкретной номенклатуры."""
        try:
            nomenclature = get_object_or_404(Nomenclature, id=pk)
        except ValidationError:
            return Response(
                {'detail': f'Значение "{pk}" не является верным UUID-ом.'},
                status=HTTP_400_BAD_REQUEST
            )
        statistics = TickerStat.objects.filter(client=pk)
        serializer = TickerStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class NomenclatureGroupViewSet(viewsets.ModelViewSet):
    """Работа с группами номенклатур."""

    queryset = NomenclatureGroup.objects.all().prefetch_related(
        'clients',
    ).select_related('owner')

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = NomenclatureGroupListSerializer
        else:
            serializer = NomenclatureGroupSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
