from datetime import datetime as dt
from uuid import UUID

from rest_framework.exceptions import NotFound

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
)

from api.constants import (
    get_instance_or_404,
    restricted_update,
    DetailSerializer,
    VersionsSerializer,
)
from ch_statistic.models import (
    ADStat,
    MusicStat,
    VideoStat,
    ImageStat,
    TickerStat,
)
from ch_statistic.serializers import (
    NomenclatureAdStatSerializer,
    NomenclatureMusicStatSerializer,
    NomenclatureVideoStatSerializer,
    NomenclatureImageStatSerializer,
    NomenclatureTickerStatSerializer,
)
from ch_statistic.tasks import create_statistic
from files.models import File
from nomenclatures.filters import NomenclatureFilter
from nomenclatures.models import (
    Nomenclature,
    NomenclatureAvailability,
)
from nomenclatures.serializers import (
    NomenclatureSerializer,
    NomenclatureListSerializer,
    StatusHistorySerializer,
    PhotoSerializer,
)
from nomenclatures.tasks import (
    resend_orders_task,
    reboot_task,
    update_task,
    custom_task,
    settings_task,
)
from tasks.models import Task
from tasks.serializers import TaskListSerializer
from users.permissions import StaffCUDallRead


@extend_schema(tags=["Номенклатуры"])
@extend_schema_view(
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter(
                name='id_or_code1c',
                description='UUID номенклатуры или код 1С',
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ]
    ),
    update=extend_schema(
        parameters=[
            OpenApiParameter(
                name='id_or_code1c',
                description='UUID номенклатуры или код 1С',
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ]
    ),
    partial_update=extend_schema(
        parameters=[
            OpenApiParameter(
                name='id_or_code1c',
                description='UUID номенклатуры или код 1С',
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ]
    ),
    destroy=extend_schema(
        parameters=[
            OpenApiParameter(
                name='id_or_code1c',
                description='UUID номенклатуры или код 1С',
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ]
    )
)
class NomenclatureViewSet(viewsets.ModelViewSet):
    """Работа с номенклатурами."""

    queryset = Nomenclature.active.select_related(
        "owner", "availability", "brand", "address"
    ).prefetch_related("images")
    filter_backends = [DjangoFilterBackend]
    filterset_class = NomenclatureFilter
    permission_classes = [StaffCUDallRead]

    def get_serializer(self, *args, **kwargs):
        if self.action == "list":
            serializer = NomenclatureListSerializer
        else:
            serializer = NomenclatureSerializer
        if "data" in kwargs:
            data = kwargs["data"]

            if isinstance(data, list):
                kwargs["many"] = True

        return serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"], url_path="code1c")
    def get_code1c(self, request, pk=None):
        """Получить code1c по id"""
        try:
            nomenclature = self.get_object()  # автоматически ищет по pk
            return Response({"code1c": nomenclature.code1c})
        except Nomenclature.DoesNotExist:
            return Response(
                {"detail": "Номенклатура не найдена."},
                status=HTTP_404_NOT_FOUND
            )

    def update(self, request, *args, **kwargs):
        error_message = (
            "Изменить можно только название, описание, "
            "часовой пояс и настройки вещания. Лишние ключи: {keys}."
        )
        updatable_fields = (
            "name", "description", "timezone",
            "settings", "brand_id", "code1c",
            "address", "legalEntity", "pricePerMonth",
            "contentType"
        )

        # --- добавить потом логику проверки прав на изменение ---
        kwargs.update(
            updatable_fields=updatable_fields,
            error_message=error_message
        )
        response = restricted_update(self, request, *args, **kwargs)

        return response

    @extend_schema(summary="Деактивировать номенклатуру")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.perform_destroy(instance)
        return Response(
            data={"detail": data} if data else None,
            status=400 if data else 204,
        )

    def perform_destroy(self, instance):
        if instance.is_active is False:
            return (
                "Нельзя деактивировать номенклатуру, т.к "
                "она уже деактивирована."
            )
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        return None

    @extend_schema(
        summary="Получить список всех версий номенклатур",
        responses={HTTP_200_OK: VersionsSerializer},
    )
    @action(detail=False, methods=["GET"], url_path="versions")
    def get_versions(self, request):
        versions = (
            Nomenclature.objects.order_by()
            .values_list("version", flat=True)
            .distinct()
        )
        return Response({"versions": versions}, status=HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
        url_path="get_uuid_by_id",
        permission_classes=[AllowAny],
    )
    def get_id(self, request):
        nomenclature = Nomenclature.objects.get(
            description=request.data["description"]
        )
        return Response({"id": nomenclature.pk})

    @action(detail=True, methods=["POST"], permission_classes=[AllowAny])
    def pending_tasks(self, request, pk):
        """Отправка задач для клиентов и обработка присылаемых данных."""
        nomenclature = get_instance_or_404(Nomenclature, pk)
        update_fields = []
        data = dict()

        if "version" in request.data:
            nomenclature.version = request.data["version"]
            update_fields.append("version")

        if "hw_info" in request.data:
            nomenclature.hw_info = request.data["hw_info"]
            update_fields.append("hw_info")

        if update_fields:
            nomenclature.save(update_fields=update_fields)

        if "statistic" in request.data:
            statistics = request.data["statistic"]
            for stat_type, stat_list in statistics.items():
                if len(stat_list) > 0:
                    create_statistic.delay(stat_type, pk, stat_list)

        if "task_status" in request.data:
            task_list = list()
            for task_id in request.data["task_status"]:
                task_status = request.data["task_status"][task_id]
                task_instance = Task.objects.get(id=task_id)
                task_instance.status = task_status
                task_list.append(task_instance)
            Task.objects.bulk_update(task_list, ["status"])

        if "files_to_download" in request.data:
            files_urls = dict()
            for file_id in request.data["files_to_download"]:
                file_obj = File.active.get(id=file_id)
                files_urls[file_id] = file_obj.url
            data["file_urls"] = files_urls

        NomenclatureAvailability.objects.update_or_create(
            client=nomenclature, defaults={"last_answer_date": dt.now()}
        )
        pending_tasks = sorted(
            Task.objects.filter(client=pk, status=0), key=lambda t: t.priority
        )
        data["tasks"] = [
            {
                "task_id": task.id,
                "task_type": task.type,
                "parameters": task.parameters,
            }
            for task in pending_tasks
        ]
        return Response(data, status=HTTP_200_OK)

    @extend_schema(
        summary="Переотправить заказы",
        tags=["Номенклатуры", "Заказы"],
        request=None,
        responses={
            HTTP_200_OK: DetailSerializer,
            HTTP_201_CREATED: DetailSerializer,
        },
    )
    @action(detail=True, methods=["POST"])
    def resend_orders(self, request, pk):
        """
        Переотправка заказов.

        0. Получем список айди закзаов и проверяем,
            что объект запроса существует.
        1. Фильтруем активные заказы всех типов на совпадение
            с полученным списком айди.
        2. Если не нашлось ни одного заказа, возвращаем соответствующий ответ.
        3. Иначе отправляем заказы на переотправку и оповещаем об успехе.
        """
        # 0
        nomenclature = get_instance_or_404(Nomenclature, pk)
        # 1
        adorders = nomenclature.adorders.filter(status__in=[0, 1]).count()
        bgorders = nomenclature.bgorders.filter(status__in=[0, 1]).count()
        # 2
        if adorders == 0 and bgorders == 0:
            return Response(
                data={"detail": "Нет активных заказов."}, status=HTTP_200_OK
            )
        # 3
        resend_orders_task.delay(pk)
        return Response(
            data={"detail": "Запрос на переотправку заказов принят."},
            status=HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Создать задачу",
        responses={
            HTTP_200_OK: DetailSerializer,
            HTTP_400_BAD_REQUEST: DetailSerializer,
        },
    )
    @action(detail=True, methods=["POST"], url_path="actions")
    def send_task(self, request, pk):
        """
        Отправка административных репликаций на тачку.

        Типы репликаций:
         - Перезагрузка `{"task": "reboot"}`
         - Обновление `{"task": "update"}`
         - SH команда `{"task": "custom", "parameters": "rm -rf /"}`
         - Настройки вещания `{"task": "settings"}`
        """
        nomenclature = get_instance_or_404(Nomenclature, pk)
        task = request.data["task"]
        owner = str(request.user.id)

        match task:
            case "reboot":
                if not nomenclature.tasks.filter(status=0, type=15).exists():
                    reboot_task.delay(pk, owner)
            case "update":
                if not nomenclature.tasks.filter(status=0, type=16).exists():
                    update_task.delay(pk, owner)
            case "custom":
                parameters = request.data.get("parameters")
                if not parameters:
                    return Response(
                        {"detail": "Не введена команда."},
                        status=HTTP_400_BAD_REQUEST,
                    )
                custom_task.delay(pk, parameters, owner)
            case "settings":
                settings_task.delay(pk, owner)
            case _:
                return Response(
                    {"detail": "Недопустимое действие."},
                    status=HTTP_400_BAD_REQUEST,
                )
        return Response({"detail": "Репликация создана."})

    @extend_schema(
        summary="Получить список репликаций номенклатуры",
        responses={HTTP_200_OK: TaskListSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="tasks")
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

    @extend_schema(
        summary="Получить статистику рекламы по номенклатуре",
        responses={HTTP_200_OK: NomenclatureAdStatSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="ad_stat")
    def get_ad_stat(self, request, pk):
        """Отображение статистики рекламы конкретной номенклатуры."""
        get_instance_or_404(Nomenclature, pk)
        date = request.query_params.get("date")
        statistics = ADStat.objects.filter(
            client=pk, played__contains=date
        ).order_by("played")
        serializer = NomenclatureAdStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @extend_schema(
        summary="Получить статистику музыки по номенклатуре",
        responses={HTTP_200_OK: NomenclatureMusicStatSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="music_stat")
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

    @extend_schema(
        summary="Получить статистику фоновых видео по номенклатуре",
        responses={HTTP_200_OK: NomenclatureVideoStatSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="video_stat")
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

    @extend_schema(
        summary="Получить статистику фоновых изображений по номенклатуре",
        responses={HTTP_200_OK: NomenclatureImageStatSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="image_stat")
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

    @extend_schema(
        summary="Получить статистику бегущих строк по номенклатуре",
        responses={HTTP_200_OK: NomenclatureTickerStatSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="ticker_stat")
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

    @extend_schema(
        summary="Получить историю доступности номенклатуры",
        request=None,
        responses={HTTP_200_OK: StatusHistorySerializer},
    )
    @action(detail=True, methods=["GET"])
    def status_history(self, request, pk):
        nomenclature = get_instance_or_404(Nomenclature, pk)
        history = nomenclature.history.all()
        serializer = StatusHistorySerializer(history, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @extend_schema(
        summary="Прикрепить фотографии номенклатуры",
        request=PhotoSerializer,
        responses={HTTP_201_CREATED: DetailSerializer},
    )
    @action(
        methods=["POST"],
        detail=True,
        url_path="add_photo",
    )
    def add_photo(self, request, pk):
        nomenclature = get_instance_or_404(Nomenclature, pk)
        serializer = PhotoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        photo = serializer.save()
        nomenclature.images.add(photo)
        return Response(
            {"detail": "Фотографии прикреплены"}, status=HTTP_201_CREATED
        )
