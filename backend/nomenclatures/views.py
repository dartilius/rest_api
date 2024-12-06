from datetime import datetime as dt
from django_filters.rest_framework import DjangoFilterBackend
from itertools import chain
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED
)

from api.constants import Constants, get_instance_or_404
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
    StatusHistorySerializer
)
from nomenclatures.models import (
    Nomenclature,
    NomenclatureAvailability
)
from nomenclatures.tasks import (
    resend_orders_task,
    reboot_task,
    update_task,
    custom_task,
    settings_task
)
from tasks.models import Task
from tasks.serializers import TaskListSerializer
from users.permissions import SuperuserDStaffCUAuthRetrieve


class NomenclatureViewSet(viewsets.ModelViewSet):
    """Работа с номенклатурами."""

    queryset = Nomenclature.objects.filter(
        is_active=True
    ).select_related('owner', 'availability')
    filter_backends = [DjangoFilterBackend]
    filterset_class = NomenclatureFilter
    permission_classes = [SuperuserDStaffCUAuthRetrieve]

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

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    @action(detail=False, methods=['GET'], url_path='versions')
    def get_versions(self, request):
        versions = Nomenclature.objects.order_by().values_list(
            'version', flat=True
        ).distinct()
        return Response(
            {'versions': versions},
            status=HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['GET'],
        url_path='get_uuid_by_id',
        permission_classes=[AllowAny]
    )
    def get_id(self, request):
        nomenclature = Nomenclature.objects.get(
            description=request.data['description']
        )
        return Response({"id": nomenclature.pk})

    @action(detail=True, methods=['GET'])
    def status_history(self, request, pk):
        nomenclature = get_instance_or_404(Nomenclature, pk)
        history = nomenclature.history.all()
        serializer = StatusHistorySerializer(history, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['POST'], permission_classes=[AllowAny])
    def pending_tasks(self, request, pk):
        """Отправка задач для клиентов и обработка присылаемых данных."""
        nomenclature = get_instance_or_404(Nomenclature, pk)
        nom_update = []

        if 'version' in request.data:
            nomenclature.version = request.data['version']
            nom_update.append('version')

        if 'hw_info' in request.data:
            nomenclature.hw_info = request.data['hw_info']
            nom_update.append('hw_info')

        if nom_update:
            nomenclature.save(update_fields=[*nom_update])

        if 'statistic' in request.data:
            statistics = request.data['statistic']
            for stat_type, stat_list in statistics.items():
                if len(stat_list) > 0:
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
            client=pk,
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
        get_instance_or_404(Nomenclature, pk)
        date = request.query_params.get('date')
        statistics = ADStat.objects.filter(
            client=pk, played__contains=date
        ).order_by('played')
        serializer = NomenclatureAdStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['GET'], url_path='music_stat')
    def get_music_stat(self, request, pk):
        """Отображение статистики музыки конкретной номенклатуры."""
        get_instance_or_404(Nomenclature, pk)
        statistics = MusicStat.objects.filter(client=pk)
        page = self.paginate_queryset(statistics)
        if page is not None:
            serializer = NomenclatureMusicStatSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = NomenclatureMusicStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['GET'], url_path='video_stat')
    def get_video_stat(self, request, pk):
        """Отображение статистики видео конкретной номенклатуры."""
        get_instance_or_404(Nomenclature, pk)
        statistics = VideoStat.objects.filter(client=pk)
        page = self.paginate_queryset(statistics)
        if page is not None:
            serializer = NomenclatureVideoStatSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NomenclatureVideoStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['GET'], url_path='image_stat')
    def get_image_stat(self, request, pk):
        """Отображение статистики картинок конкретной номенклатуры."""
        get_instance_or_404(Nomenclature, pk)
        statistics = ImageStat.objects.filter(client=pk)
        page = self.paginate_queryset(statistics)
        if page is not None:
            serializer = NomenclatureImageStatSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = NomenclatureImageStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['GET'], url_path='ticker_stat')
    def get_ticker_stat(self, request, pk):
        """Отображение статистики бегущих строк конкретной номенклатуры."""
        get_instance_or_404(Nomenclature, pk)
        statistics = TickerStat.objects.filter(client=pk)
        page = self.paginate_queryset(statistics)
        if page is not None:
            serializer = NomenclatureTickerStatSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = NomenclatureTickerStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def resend_orders(self, request, pk):
        """
        Переотправка заказов.

        0. Получаем список заказов на переотправку.
        1. Проверяем, что заказы в списке активны.
        1.1. Активные заказы сериализуются в JSON и отправляются в целери
            для создания соответствующих репликаций в фоне.
        1.2. Заказы, которые нельзя переотправить,
            записываем в отдельный список.
        2. В ответ отдаём сообщение со списком заказов которые будут
            переотправлены и которые переотправить нельзя.
        """
        nomenclature = get_instance_or_404(Nomenclature, pk)
        empty_values = Constants.empty_values
        orders = chain(
            nomenclature.adorders.filter(status__in=[0, 1]),
            nomenclature.bgorders.filter(status__in=[0, 1])
        )

        if list(orders) in empty_values:
            result_text = 'Нет активных заказов.'
            return Response(data=result_text, status=HTTP_200_OK)

        order_ids = [order.id for order in orders]
        resend_orders_task.delay(order_ids)

        result_text = 'Запрос на переотправку заказов принят.'
        return Response(data=result_text, status=HTTP_201_CREATED)

    @action(detail=True, methods=['POST'], url_path='actions')
    def send_task(self, request, pk):
        """
        Отправка административных репликаций на тачку.

        Типы репликаций:
         - Перезагрузка
         - Обновление
         - SH команда
            parameters = {'command': 'rm -rf /'}
         - Настройки вещания
            settings = {'mon' = {'default_volume': [50, 50, 50, 50], ...}
        """
        nomenclature = get_instance_or_404(Nomenclature, pk)
        task = request.data['task']
        owner = str(request.user.id)

        match task:
            case 'reboot':
                if not nomenclature.tasks.filter(status=0, type=15).exists():
                    reboot_task.delay(pk, owner)
            case 'update':
                if not nomenclature.tasks.filter(status=0, type=16).exists():
                    update_task.delay(pk, owner)
            case 'custom':
                parameters = request.data['parameters']
                custom_task.delay(pk, parameters, owner)
            case 'settings':
                settings = request.data['settings']
                settings_task.delay(pk, settings, owner)

    @action(detail=True, methods=['POST'], url_path='tasks')
    def get_tasks(self, request, pk):
        """Запрос списка репликаций номенклатуры."""
        get_instance_or_404(Nomenclature, pk)
        tasks = Task.objects.filter(client=pk)

        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
