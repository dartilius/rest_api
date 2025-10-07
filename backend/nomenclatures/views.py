# backend/nomenclatures/views.py
from datetime import datetime as dt
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
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
    Brand,
    NomenclatureImage
)
from nomenclatures.serializers import (
    NomenclatureSerializer,
    NomenclatureListSerializer,
    StatusHistorySerializer,
    PhotoSerializer,
    BrandSerializer,
    BrandCreateSerializer,
)
from nomenclatures.tasks import (
    resend_orders_task,
    reboot_task,
    update_task,
    custom_task,
    settings_task,
)
from orders.views import NoDeleteViewSet
from tasks.models import Task
from tasks.serializers import TaskListSerializer
from users.permissions import StaffCUDallRead


@extend_schema(tags=["Номенклатуры"])
class NomenclatureViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с номенклатурами.

    Предоставляет CRUD операции для номенклатур, а также дополнительные
    методы для управления задачами, статистикой и состоянием устройств.
    Поддерживает создание/прикрепление брендов через get_or_create.

    Attributes:
        queryset (QuerySet): Оптимизированный queryset с prefetch_related
        filter_backends (list): Список бэкендов фильтрации
        filterset_class (NomenclatureFilter): Класс фильтрации
        permission_classes (list): Классы разрешений
    """

    queryset = Nomenclature.active.select_related(
        "owner", "availability", "brand", "address"
    ).prefetch_related(
        Prefetch('images',
                 queryset=NomenclatureImage.objects.filter(type='interior'),
                 to_attr='interior_images'),
        Prefetch('images',
                 queryset=NomenclatureImage.objects.filter(type='exterior'),
                 to_attr='exterior_images')
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = NomenclatureFilter
    permission_classes = [StaffCUDallRead]

    def get_serializer(self, *args, **kwargs):
        """
        Возвращает соответствующий сериализатор в зависимости от действия.

        Для списка использует NomenclatureListSerializer, для детального
        просмотра и операций записи - NomenclatureSerializer.

        Args:
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Serializer: Соответствующий сериализатор
        """
        if self.action == "list":
            serializer = NomenclatureListSerializer
        else:
            serializer = NomenclatureSerializer

        if "data" in kwargs:
            data = kwargs["data"]
            if isinstance(data, list):
                kwargs["many"] = True

        return serializer(*args, **kwargs)

    def get_queryset(self):
        """
        Возвращает оптимизированный queryset с кэшированием.

        Кэширует результаты запроса с учетом параметров фильтрации
        для улучшения производительности при повторных запросах.

        Returns:
            QuerySet: Оптимизированный queryset номенклатур
        """
        cache_key = f'nomenclature_list_{self.request.GET.urlencode()}'
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return cached_data

        queryset = super().get_queryset()
        cache.set(cache_key, queryset, timeout=300)  # Кэшируем на 5 минут
        return queryset

    def perform_create(self, serializer):
        """
        Сохраняет новую номенклатуру и инвалидирует кэш.

        Обработка бренда происходит в сериализаторе через get_or_create,
        поэтому здесь просто сохраняем объект.

        Args:
            serializer: Сериализатор с валидированными данными
        """
        serializer.save(owner=self.request.user)
        # Инвалидируем кэш при создании новой номенклатуры
        cache.delete_pattern('nomenclature_list_*')

    def update(self, request, *args, **kwargs):
        """
        Обновляет номенклатуру и инвалидирует кэш.

        Обработка бренда происходит в сериализаторе через get_or_create.

        Args:
            request: HTTP запрос
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Response: Ответ с обновленными данными
        """
        response = super().update(request, *args, **kwargs)
        # Инвалидируем кэш при обновлении
        cache.delete_pattern('nomenclature_list_*')
        return response

    def destroy(self, request, *args, **kwargs):
        """
        Удаляет номенклатуру и инвалидирует кэш.

        Args:
            request: HTTP запрос
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Response: Ответ с результатом удаления
        """
        response = super().destroy(request, *args, **kwargs)
        # Инвалидируем кэш при удалении
        cache.delete_pattern('nomenclature_list_*')
        return response

    @extend_schema(summary="Деактивировать номенклатуру")
    def destroy(self, request, *args, **kwargs):
        """
        Деактивирует номенклатуру (мягкое удаление).

        Args:
            request: HTTP запрос
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Response: Ответ с результатом деактивации
        """
        instance = self.get_object()
        data = self.perform_destroy(instance)
        return Response(
            data={"detail": data} if data else None,
            status=400 if data else 204,
        )

    def perform_destroy(self, instance):
        """
        Выполняет деактивацию номенклатуры.

        Args:
            instance: Объект номенклатуры

        Returns:
            str | None: Сообщение об ошибке или None при успехе
        """
        if instance.is_active is False:
            return "Нельзя деактивировать номенклатуру, т.к она уже деактивирована."
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        return None

    @extend_schema(
        summary="Получить список всех версий номенклатур",
        responses={HTTP_200_OK: VersionsSerializer},
    )
    @action(detail=False, methods=["GET"], url_path="versions")
    @method_decorator(cache_page(60*60))  # Кэшируем на 1 час
    def get_versions(self, request):
        """
        Возвращает список всех уникальных версий номенклатур.

        Args:
            request: HTTP запрос

        Returns:
            Response: Список версий в формате {"versions": [...]}
        """
        cache_key = 'nomenclature_versions'
        versions = cache.get(cache_key)

        if versions is None:
            versions = list(Nomenclature.objects.order_by()
                          .values_list("version", flat=True)
                          .distinct())
            cache.set(cache_key, versions, timeout=3600)

        return Response({"versions": versions}, status=HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
        url_path="get_uuid_by_id",
        permission_classes=[AllowAny],
    )
    def get_id(self, request):
        """
        Получает UUID номенклатуры по описанию.

        Args:
            request: HTTP запрос с description в теле

        Returns:
            Response: UUID номенклатуры в формате {"id": "uuid"}
        """
        nomenclature = Nomenclature.objects.get(
            description=request.data["description"]
        )
        return Response({"id": nomenclature.pk})

    @action(detail=True, methods=["POST"], permission_classes=[AllowAny])
    def pending_tasks(self, request, pk):
        """
        Обрабатывает входящие задачи от клиентов и возвращает pending задачи.

        Args:
            request: HTTP запрос с данными от клиента
            pk: UUID номенклатуры

        Returns:
            Response: Данные для клиента с задачами и URL файлов
        """
        nomenclature = get_instance_or_404(Nomenclature, pk)
        update_fields = []
        data = dict()

        # Обновление версии и информации о железе
        if "version" in request.data:
            nomenclature.version = request.data["version"]
            update_fields.append("version")

        if "hw_info" in request.data:
            nomenclature.hw_info = request.data["hw_info"]
            update_fields.append("hw_info")

        if update_fields:
            nomenclature.save(update_fields=update_fields)

        # Обработка статистики
        if "statistic" in request.data:
            statistics = request.data["statistic"]
            for stat_type, stat_list in statistics.items():
                if len(stat_list) > 0:
                    create_statistic.delay(stat_type, pk, stat_list)

        # Обновление статусов задач
        if "task_status" in request.data:
            task_ids = list(request.data["task_status"].keys())
            # Оптимизация: один запрос вместо множественных
            tasks = Task.objects.filter(id__in=task_ids)
            task_list = []
            for task in tasks:
                task_status = request.data["task_status"][str(task.id)]
                task.status = task_status
                task_list.append(task)
            Task.objects.bulk_update(task_list, ["status"])

        # Подготовка URL файлов для загрузки
        if "files_to_download" in request.data:
            file_ids = request.data["files_to_download"]
            # Оптимизация: один запрос вместо множественных
            files = File.active.filter(id__in=file_ids)
            files_urls = {str(file.id): file.url for file in files}
            data["file_urls"] = files_urls

        # Обновление времени последнего ответа
        NomenclatureAvailability.objects.update_or_create(
            client=nomenclature, defaults={"last_answer_date": dt.now()}
        )

        # Получение pending задач с оптимизацией
        pending_tasks = Task.objects.filter(client=pk, status=0)\
                                  .select_related('owner', 'client')\
                                  .order_by('priority')

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
        Переотправляет активные заказы на номенклатуру.

        Args:
            request: HTTP запрос
            pk: UUID номенклатуры

        Returns:
            Response: Результат операции переотправки
        """
        nomenclature = get_instance_or_404(Nomenclature, pk)

        # Проверка активных заказов
        adorders = nomenclature.adorders.filter(status__in=[0, 1]).count()
        bgorders = nomenclature.bgorders.filter(status__in=[0, 1]).count()

        if adorders == 0 and bgorders == 0:
            return Response(
                data={"detail": "Нет активных заказов."}, status=HTTP_200_OK
            )

        # Запуск задачи переотправки
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
        Создает административные задачи для номенклатуры.

        Поддерживаемые типы задач:
        - reboot: Перезагрузка
        - update: Обновление
        - custom: Выполнение SH команды
        - settings: Отправка настроек вещания

        Args:
            request: HTTP запрос с параметрами задачи
            pk: UUID номенклатуры

        Returns:
            Response: Результат создания задачи
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
        """
        Возвращает список задач для номенклатуры.

        Args:
            request: HTTP запрос
            pk: UUID номенклатуры

        Returns:
            Response: Список задач с пагинацией
        """
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
    @method_decorator(cache_page(60*5))  # Кэшируем на 5 минут
    def get_ad_stat(self, request, pk):
        """
        Возвращает статистику рекламы для номенклатуры.

        Args:
            request: HTTP запрос с параметром date
            pk: UUID номенклатуры

        Returns:
            Response: Статистика рекламы
        """
        get_instance_or_404(Nomenclature, pk)
        date = request.query_params.get("date")
        cache_key = f'ad_stat_{pk}_{date}'

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=HTTP_200_OK)

        statistics = ADStat.objects.filter(
            client=pk, played__contains=date
        ).order_by("played")

        serializer = NomenclatureAdStatSerializer(statistics, many=True)
        response_data = serializer.data
        cache.set(cache_key, response_data, timeout=300)

        return Response(response_data, status=HTTP_200_OK)

    @extend_schema(
        summary="Получить статистику музыки по номенклатуре",
        responses={HTTP_200_OK: NomenclatureMusicStatSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="music_stat")
    @method_decorator(cache_page(60*5))  # Кэшируем на 5 минут
    def get_music_stat(self, request, pk):
        """
        Возвращает статистику музыки для номенклатуры.

        Args:
            request: HTTP запрос
            pk: UUID номенклатуры

        Returns:
            Response: Статистика музыки
        """
        get_instance_or_404(Nomenclature, pk)
        cache_key = f'music_stat_{pk}'

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=HTTP_200_OK)

        statistics = MusicStat.objects.filter(client=pk)
        page = self.paginate_queryset(statistics)

        if page is not None:
            serializer = NomenclatureMusicStatSerializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
            cache.set(cache_key, response_data, timeout=300)
            return Response(response_data, status=HTTP_200_OK)

        serializer = NomenclatureMusicStatSerializer(statistics, many=True)
        response_data = serializer.data
        cache.set(cache_key, response_data, timeout=300)

        return Response(response_data, status=HTTP_200_OK)

    @extend_schema(
        summary="Получить статистику фоновых видео по номенклатуре",
        responses={HTTP_200_OK: NomenclatureVideoStatSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="video_stat")
    @method_decorator(cache_page(60*5))  # Кэшируем на 5 минут
    def get_video_stat(self, request, pk):
        """
        Возвращает статистику фоновых видео для номенклатуры.

        Args:
            request: HTTP запрос
            pk: UUID номенклатуры

        Returns:
            Response: Статистика видео
        """
        get_instance_or_404(Nomenclature, pk)
        cache_key = f'video_stat_{pk}'

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=HTTP_200_OK)

        statistics = VideoStat.objects.filter(client=pk)
        page = self.paginate_queryset(statistics)

        if page is not None:
            serializer = NomenclatureVideoStatSerializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
            cache.set(cache_key, response_data, timeout=300)
            return Response(response_data, status=HTTP_200_OK)

        serializer = NomenclatureVideoStatSerializer(statistics, many=True)
        response_data = serializer.data
        cache.set(cache_key, response_data, timeout=300)

        return Response(response_data, status=HTTP_200_OK)

    @extend_schema(
        summary="Получить статистику фоновых изображений по номенклатуре",
        responses={HTTP_200_OK: NomenclatureImageStatSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="image_stat")
    @method_decorator(cache_page(60*5))  # Кэшируем на 5 минут
    def get_image_stat(self, request, pk):
        """
        Возвращает статистику фоновых изображений для номенклатуры.

        Args:
            request: HTTP запрос
            pk: UUID номенклатуры

        Returns:
            Response: Статистика изображений
        """
        get_instance_or_404(Nomenclature, pk)
        cache_key = f'image_stat_{pk}'

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=HTTP_200_OK)

        statistics = ImageStat.objects.filter(client=pk)
        page = self.paginate_queryset(statistics)

        if page is not None:
            serializer = NomenclatureImageStatSerializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
            cache.set(cache_key, response_data, timeout=300)
            return Response(response_data, status=HTTP_200_OK)

        serializer = NomenclatureImageStatSerializer(statistics, many=True)
        response_data = serializer.data
        cache.set(cache_key, response_data, timeout=300)

        return Response(response_data, status=HTTP_200_OK)

    @extend_schema(
        summary="Получить статистику бегущих строк по номенклатуре",
        responses={HTTP_200_OK: NomenclatureTickerStatSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="ticker_stat")
    @method_decorator(cache_page(60*5))  # Кэшируем на 5 минут
    def get_ticker_stat(self, request, pk):
        """
        Возвращает статистику бегущих строк для номенклатуры.

        Args:
            request: HTTP запрос
            pk: UUID номенклатуры

        Returns:
            Response: Статистика бегущих строк
        """
        get_instance_or_404(Nomenclature, pk)
        cache_key = f'ticker_stat_{pk}'

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=HTTP_200_OK)

        statistics = TickerStat.objects.filter(client=pk)
        page = self.paginate_queryset(statistics)

        if page is not None:
            serializer = NomenclatureTickerStatSerializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
            cache.set(cache_key, response_data, timeout=300)
            return Response(response_data, status=HTTP_200_OK)

        serializer = NomenclatureTickerStatSerializer(statistics, many=True)
        response_data = serializer.data
        cache.set(cache_key, response_data, timeout=300)

        return Response(response_data, status=HTTP_200_OK)

    @extend_schema(
        summary="Получить историю доступности номенклатуры",
        request=None,
        responses={HTTP_200_OK: StatusHistorySerializer},
    )
    @action(detail=True, methods=["GET"])
    def status_history(self, request, pk):
        """
        Возвращает историю изменений статуса доступности номенклатуры.

        Args:
            request: HTTP запрос
            pk: UUID номенклатуры

        Returns:
            Response: История статусов
        """
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
        """
        Добавляет фотографии к номенклатуре.

        Args:
            request: HTTP запрос с данными фотографии
            pk: UUID номенклатуры

        Returns:
            Response: Результат добавления фотографии
        """
        nomenclature = get_instance_or_404(Nomenclature, pk)
        serializer = PhotoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        photo = serializer.save()
        nomenclature.images.add(photo)

        # Инвалидируем кэш, так как изменились данные номенклатуры
        cache.delete_pattern('nomenclature_list_*')

        return Response(
            {"detail": "Фотографии прикреплены"}, status=HTTP_201_CREATED
        )


@extend_schema(tags=["Бренды"])
class BrandViewSet(NoDeleteViewSet):
    """
    ViewSet для работы с брендами.

    Предоставляет CRUD операции для брендов с ограничениями на удаление.
    Использует get_or_create для избежания дубликатов при создании.

    Attributes:
        queryset (QuerySet): QuerySet всех брендов
        permission_classes (list): Классы разрешений
    """

    queryset = Brand.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        """
        Возвращает соответствующий сериализатор в зависимости от действия.

        Returns:
            Serializer: BrandCreateSerializer для операций записи,
                       BrandSerializer для операций чтения
        """
        if self.action in ["create", "update", "partial_update"]:
            return BrandCreateSerializer
        return BrandSerializer

    def perform_create(self, serializer):
        """
        Создает бренд или возвращает существующий с таким же именем.

        Использует get_or_create для избежания дубликатов брендов.

        Args:
            serializer: Сериализатор с валидированными данными

        Returns:
            Brand: Созданный или найденный бренд
        """
        name = serializer.validated_data['name']
        logo = serializer.validated_data.get('logo')
        
        # Используем get_or_create для поиска существующего бренда или создания нового
        brand, created = Brand.objects.get_or_create(
            name=name,
            defaults={'logo': logo} if logo else {}
        )
        
        # Если бренд уже существовал и передан новый логотип - обновляем
        if not created and logo:
            brand.logo = logo
            brand.save()

        return brand

    @method_decorator(cache_page(60*60))  # Кэшируем на 1 час
    def list(self, request, *args, **kwargs):
        """
        Возвращает список брендов с кэшированием.

        Args:
            request: HTTP запрос
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Response: Список брендов
        """
        return super().list(request, *args, **kwargs)
