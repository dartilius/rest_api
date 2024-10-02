from datetime import datetime as dt
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.permissions import AllowAny
from ch_statistic.models import (
    ADStat,
    MusicStat,
    VideoStat,
    ImageStat,
    TickerStat
)
from ch_statistic.serializers import (
    NomenclatureAdStatSerializer,
    NomenclatureMusicStatSerializer,
    NomenclatureVideoStatSerializer,
    NomenclatureImageStatSerializer,
    NomenclatureTickerStatSerializer
)
from ch_statistic.tasks import create_statistic
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
    NomenclatureGroup,
    NomenclatureAvailability
)
from tasks.models import Task


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
        serializer.save(owner=self.request.user)

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
        instance.is_active = False

    # пока оставлю
    # @action(detail=True, methods=['POST'], url_path='is_active')
    # def toggle_is_active(self, request, pk):
    #     try:
    #         nomenclature = get_object_or_404(Nomenclature, id=pk)
    #     except ValidationError:
    #         return Response(
    #             {'detail': f'Значение "{pk}" не является верным UUID-ом.'},
    #             status=HTTP_400_BAD_REQUEST
    #         )
    #     if nomenclature.is_active is True:
    #         self.perform_destroy(nomenclature)
    #         status = 'деактивированна'
    #     else:
    #         nomenclature.is_active = True
    #         group = NomenclatureGroup.objects.create(
    #             owner=nomenclature.owner,
    #             name=nomenclature.name,
    #         )
    #         group.clients.add(nomenclature)
    #         group.save()
    #         nomenclature.save()
    #         status = 'активна'
    #     return Response(f'Номенклатура {status}', status=HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def status_history(self, request, pk):
        try:
            nomenclature = get_object_or_404(Nomenclature, id=pk)
        except ValidationError:
            return Response(
                {'detail': f'Значение "{pk}" не является верным UUID-ом.'},
                status=HTTP_400_BAD_REQUEST
            )
        history = nomenclature.history.all()
        serializer = StatusHistorySerializer(history, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['POST'], permission_classes=[AllowAny])
    def pending_tasks(self, request, pk):
        """Отдача задач для клиентов и обработка присылаемых данных."""
        try:
            nomenclature = get_object_or_404(Nomenclature, id=pk)
        except ValidationError:
            return Response(
                {'detail': f'Значение "{pk}" не является верным UUID-ом.'},
                status=HTTP_400_BAD_REQUEST
            )
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
                create_statistic.delay(stat_type, pk, stat_list)

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

    @action(detail=True, methods=['GET'], url_path='ad_stat')
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
        serializer = NomenclatureAdStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['GET'], url_path='music_stat')
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
        serializer = NomenclatureMusicStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['GET'],url_path='video_stat')
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
        serializer = NomenclatureVideoStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['GET'], url_path='image_stat')
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
        serializer = NomenclatureImageStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['GET'], url_path='ticker_stat')
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
        serializer = NomenclatureTickerStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class NomenclatureGroupViewSet(viewsets.ModelViewSet):
    """Работа с группами номенклатур."""

    queryset = NomenclatureGroup.objects.all().prefetch_related(
        'clients'
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
