# orders/views.py
# -*- coding: utf-8 -*-

"""
REST API для управления рекламными и фоновыми заказами.

Модуль предоставляет два ViewSet:

1. AdOrderViewSet
   Управляет рекламными заказами.

2. BgOrderViewSet
   Управляет фоновыми заказами.

Поддерживаемые операции:

- GET    /api/adorders/
- GET    /api/adorders/{id}/
- POST   /api/adorders/
- PATCH  /api/adorders/{id}/
- DELETE /api/adorders/{id}/cancel/

- GET    /api/bgorders/
- GET    /api/bgorders/{id}/
- POST   /api/bgorders/
- PATCH  /api/bgorders/{id}/
- DELETE /api/bgorders/{id}/cancel/

Форматы времени:

- start_time: HH:MM:SS
- end_time: HH:MM:SS
- timedelta: HH:MM:SS
- broadcast_interval.lower: YYYY-MM-DD HH:MM:SS
- broadcast_interval.upper: YYYY-MM-DD HH:MM:SS

После создания, обновления или отмены заказа создаётся Celery-задание,
которое затем передаётся клиентскому ПО.

Celery запускается через transaction.on_commit(). Это гарантирует, что
worker увидит заказ только после успешной фиксации транзакции в базе.
"""

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    extend_schema_view,
)

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
)

from api.constants import (
    DEFAULT_SCHEMA_EXAMPLES,
    DEFAULT_SCHEMA_RESPONSES,
    DetailSerializer,
    restricted_update,
)

from orders.filters import (
    AdOrderFilter,
    BgOrderFilter,
)

from orders.models import (
    AdOrder,
    BgOrder,
)

from orders.serializers import (
    AdOrderListSerializer,
    AdOrderSerializer,
    BgOrderListSerializer,
    BgOrderSerializer,
)

from orders.tasks import (
    cancel_ad_order_task,
    cancel_bg_order_task,
    create_ad_order_task,
    create_bg_order_task,
    update_ad_order_task,
    update_bg_order_task,
)

from users.permissions import StaffCUDAuthRetrieve


# =============================================================================
# Вспомогательные функции
# =============================================================================


def _normalize_created_orders(value):
    """
    Приводит результат serializer.save() к плоскому списку заказов.

    Причина существования функции:

    AdOrderSerializer.create() и BgOrderSerializer.create() создают по одному
    заказу для каждого выбранного клиента и возвращают список объектов.

    Если API получил список входных объектов и сериализатор работает с
    many=True, DRF может вернуть список списков:

        [
            [order_1, order_2],
            [order_3]
        ]

    Функция преобразует такой результат в:

        [order_1, order_2, order_3]

    Args:
        value:
            Один объект заказа, список заказов либо список списков.

    Returns:
        list:
            Плоский список объектов AdOrder или BgOrder.
    """
    if value is None:
        return []

    if not isinstance(value, (list, tuple)):
        return [value]

    result = []

    for item in value:
        if isinstance(item, (list, tuple)):
            result.extend(item)
        else:
            result.append(item)

    return result


def _enqueue_after_commit(task, *args, **kwargs):
    """
    Запускает Celery-задачу после успешного commit транзакции.

    Без transaction.on_commit() Celery worker иногда может начать выполнение
    раньше, чем созданный или изменённый заказ станет виден в базе данных.

    Args:
        task:
            Celery-задача, например create_ad_order_task.

        *args:
            Позиционные аргументы Celery-задачи.

        **kwargs:
            Именованные аргументы Celery-задачи.
    """
    transaction.on_commit(
        lambda: task.delay(*args, **kwargs)
    )


# =============================================================================
# Базовый ViewSet
# =============================================================================


class NoDeleteViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Базовый ViewSet без стандартного физического удаления объектов.

    Стандартный endpoint:

        DELETE /api/orders/{id}/

    не поддерживается.

    Вместо физического удаления используется отдельное действие cancel(),
    которое меняет статус заказа и создаёт задание отмены для клиентского ПО.
    """

    pass


# =============================================================================
# Рекламные заказы
# =============================================================================


@extend_schema_view(
    create=extend_schema(
        summary='Создать рекламный заказ',
        description=(
            'Создаёт рекламный заказ для одного или нескольких клиентов.\n\n'
            'Временные параметры start_time, end_time и timedelta '
            'передаются строками HH:MM:SS.\n\n'
            'После сохранения заказа создаётся Celery-задание типа 4 '
            'для передачи заказа клиентскому ПО.'
        ),
        request=AdOrderSerializer,
        examples=[
            OpenApiExample(
                name='Реклама в фиксированное время',
                request_only=True,
                value={
                    'name': 'Рекламный заказ',
                    'description': 'Пример рекламного заказа',
                    'clients': [
                        '5778e050-454d-4e5e-ae0f-bb584979552c'
                    ],
                    'playlist': '5cd982f9-8d14-40a1-9acb-c6a1cf6654f4',
                    'slides': None,
                    'broadcast_interval': {
                        'lower': '2026-08-17 16:00:00',
                        'upper': '2026-08-19 17:00:00',
                    },
                    'broadcast_type': 3,
                    'parameters': {
                        'times_in_hour': 3,
                        'weight': 70,
                        'start_time': '16:00:00',
                        'end_time': '17:00:00',
                    },
                },
            ),
        ],
        responses={
            HTTP_201_CREATED: AdOrderSerializer,
        } | DEFAULT_SCHEMA_RESPONSES,
    ),
    partial_update=extend_schema(
        summary='Частично обновить рекламный заказ',
        description=(
            'Разрешено изменять только name, description, playlist и slides.\n\n'
            'Если изменён playlist или slides, создаётся Celery-задание '
            'для обновления плейлиста на клиентском ПО.'
        ),
        examples=DEFAULT_SCHEMA_EXAMPLES + [
            OpenApiExample(
                name='Обновление рекламного заказа',
                request_only=True,
                value={
                    'name': 'Новое название',
                    'description': 'Новое описание',
                    'playlist': '40e6215d-b5c6-4896-987c-f30f3678f608',
                    'slides': {
                        '6ecd8c99-4036-403d-bf84-cf8400f67836': [
                            '3f333df6-90a4-4fda-8dd3-9485d27cee36'
                        ],
                    },
                },
            ),
        ],
        responses={
            HTTP_200_OK: AdOrderSerializer,
        } | DEFAULT_SCHEMA_RESPONSES,
    ),
    list=extend_schema(
        summary='Получить список рекламных заказов',
        description=(
            'Возвращает пагинированный список рекламных заказов.\n\n'
            'Поддерживаются фильтры status, owner, name, client, brc_type, '
            'created, since и until.'
        ),
        responses={
            HTTP_200_OK: AdOrderListSerializer(many=True),
        } | DEFAULT_SCHEMA_RESPONSES,
    ),
    retrieve=extend_schema(
        summary='Получить рекламный заказ',
        description=(
            'Возвращает полную информацию о рекламном заказе, включая '
            'интервал вещания, тип вещания, параметры, плейлист и слайды.'
        ),
        responses={
            HTTP_200_OK: AdOrderSerializer,
        } | DEFAULT_SCHEMA_RESPONSES,
    ),
)
@extend_schema(tags=['AD Orders'])
class AdOrderViewSet(NoDeleteViewSet):
    """
    ViewSet рекламных заказов.

    Типы вещания:

        0 — по времени работы точки;
        1 — открытие + смещение;
        2 — закрытие - смещение;
        3 — фиксированные часы;
        4 — с открытия до указанного времени;
        5 — с указанного времени до закрытия;
        6 — запуск по событию.

    Тип 6 сохраняется на backend, но клиентское ПО пока использует для него
    заглушку и не запускает такую рекламу автоматически.

    Параметры рекламного заказа:

        times_in_hour:
            Количество рекламных выходов в час.
            Допустимые значения: 1, 2, 3, 4, 6, 12.

        weight:
            Приоритет ролика от 0 до 100.

        timedelta:
            Смещение от открытия или закрытия в формате HH:MM:SS.
            Используется типами 1 и 2.

        start_time:
            Время начала в формате HH:MM:SS.
            Используется типами 3 и 5.

        end_time:
            Время окончания в формате HH:MM:SS.
            Используется типами 3 и 4.
    """

    queryset = (
        AdOrder.objects
        .all()
        .select_related(
            'owner',
            'client',
            'client__brand',
            'client__typeOfPlace',
            'client__address__address__city__locality_type',
            'client__address__address__street__street_type',
            'playlist',
        )
    )

    serializer_class = AdOrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdOrderFilter
    permission_classes = [StaffCUDAuthRetrieve]

    # PUT и обычный DELETE запрещены.
    # Обновление выполняется через PATCH, отмена — через /cancel/.
    http_method_names = [
        'get',
        'post',
        'patch',
        'delete',
        'head',
        'options',
    ]

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от текущего действия.

        Returns:
            type[serializers.Serializer]:
                AdOrderListSerializer для списка;
                AdOrderSerializer для остальных действий.
        """
        if self.action == 'list':
            return AdOrderListSerializer

        return AdOrderSerializer

    def get_serializer(self, *args, **kwargs):
        """
        Создаёт экземпляр сериализатора.

        Если POST содержит список объектов, автоматически устанавливает
        many=True. При обычном словаре используется стандартный одиночный
        сериализатор.
        """
        if isinstance(kwargs.get('data'), list):
            kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Создаёт рекламные заказы.

        Последовательность:

        1. Входные данные валидируются AdOrderSerializer.
        2. Для каждого клиента создаётся отдельный AdOrder.
        3. Результат приводится к плоскому списку.
        4. После commit запускается create_ad_order_task.
        5. Клиенту возвращается созданный заказ или список заказов.

        Args:
            request:
                HTTP-запрос с данными заказа.

        Returns:
            Response:
                HTTP 201 и созданный заказ либо список заказов.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        saved_result = serializer.save(owner=request.user)
        orders = _normalize_created_orders(saved_result)

        if not orders:
            return Response(
                {
                    'detail': (
                        'Не создано ни одного рекламного заказа. '
                        'Проверьте список clients.'
                    ),
                },
                status=HTTP_400_BAD_REQUEST,
            )

        order_ids = [
            str(order.id)
            for order in orders
        ]

        _enqueue_after_commit(
            create_ad_order_task,
            order_ids,
        )

        serializer_context = self.get_serializer_context()

        if len(orders) == 1:
            response_serializer = AdOrderSerializer(
                orders[0],
                context=serializer_context,
            )
        else:
            response_serializer = AdOrderListSerializer(
                orders,
                many=True,
                context=serializer_context,
            )

        return Response(
            response_serializer.data,
            status=HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """
        Частично обновляет рекламный заказ.

        Разрешённые поля:

        - name;
        - description;
        - playlist;
        - slides.

        Если изменены playlist или slides, после успешного commit создаётся
        Celery-задание update_ad_order_task.

        Args:
            request:
                HTTP PATCH-запрос.

        Returns:
            Response:
                Результат restricted_update().
        """
        error_message = (
            'Изменить можно только название, описание, '
            'плейлист и слайды. Лишние ключи: {keys}.'
        )

        updatable_fields = (
            'name',
            'description',
            'playlist',
            'slides',
        )

        kwargs.update(
            updatable_fields=updatable_fields,
            error_message=error_message,
        )

        response = restricted_update(
            self,
            request,
            *args,
            **kwargs,
        )

        update_succeeded = (
            HTTP_200_OK <= response.status_code < 300
        )

        replication_required = (
            'playlist' in request.data
            or 'slides' in request.data
        )

        if update_succeeded and replication_required:
            instance = self.get_object()

            _enqueue_after_commit(
                update_ad_order_task,
                order_id=str(instance.id),
            )

        return response

    @extend_schema(
        summary='Отменить рекламный заказ',
        description=(
            'Отменяет рекламный заказ и создаёт задание отмены для ПО.\n\n'
            'Отменить можно только заказ со статусом 0 или 1.'
        ),
        responses={
            HTTP_200_OK: DetailSerializer,
            HTTP_400_BAD_REQUEST: DetailSerializer,
        } | DEFAULT_SCHEMA_RESPONSES,
    )
    @action(detail=True, methods=['delete'])
    def cancel(self, request, pk=None):
        """
        Отменяет рекламный заказ.

        Перед созданием Celery-задания:

        1. Проверяется существование заказа.
        2. Выполняется объектная проверка permissions через get_object().
        3. Проверяется текущий статус заказа.

        Args:
            request:
                HTTP DELETE-запрос.

            pk:
                UUID рекламного заказа.

        Returns:
            Response:
                HTTP 200, если запрос принят;
                HTTP 400, если заказ уже завершён или отменён.
        """
        order = self.get_object()

        if order.status not in (0, 1):
            return Response(
                {
                    'detail': (
                        'Отменить можно только ожидающий '
                        'или находящийся в эфире заказ.'
                    ),
                },
                status=HTTP_400_BAD_REQUEST,
            )

        _enqueue_after_commit(
            cancel_ad_order_task,
            str(order.id),
        )

        return Response(
            {
                'message': (
                    'Запрос на отмену рекламного заказа принят.'
                ),
            },
            status=HTTP_200_OK,
        )


# =============================================================================
# Фоновые заказы
# =============================================================================


@extend_schema_view(
    create=extend_schema(
        summary='Создать фоновый заказ',
        description=(
            'Создаёт фоновый заказ для одного или нескольких клиентов.\n\n'
            'После сохранения создаётся Celery-задание соответствующего '
            'типа для передачи заказа клиентскому ПО.'
        ),
        request=BgOrderSerializer,
        examples=[
            OpenApiExample(
                name='Фоновая музыка',
                request_only=True,
                value={
                    'name': 'Фоновая музыка',
                    'description': 'Основной музыкальный плейлист',
                    'clients': [
                        '5778e050-454d-4e5e-ae0f-bb584979552c'
                    ],
                    'playlist': '3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c',
                    'order_type': 0,
                    'is_permanent': False,
                    'broadcast_interval': {
                        'lower': '2026-08-17 09:00:00',
                        'upper': '2026-08-19 21:00:00',
                    },
                    'parameters': {},
                },
            ),
        ],
        responses={
            HTTP_201_CREATED: BgOrderSerializer,
        } | DEFAULT_SCHEMA_RESPONSES,
    ),
    partial_update=extend_schema(
        summary='Частично обновить фоновый заказ',
        description=(
            'Разрешено изменять только name, description и playlist.\n\n'
            'При изменении playlist создаётся задание обновления '
            'для клиентского ПО.'
        ),
        responses={
            HTTP_200_OK: BgOrderSerializer,
        } | DEFAULT_SCHEMA_RESPONSES,
    ),
    list=extend_schema(
        summary='Получить список фоновых заказов',
        description=(
            'Возвращает пагинированный список фоновых заказов.\n\n'
            'Поддерживаются фильтры status, order_type, owner, name, client, '
            'created, since и until.'
        ),
        responses={
            HTTP_200_OK: BgOrderListSerializer(many=True),
        } | DEFAULT_SCHEMA_RESPONSES,
    ),
    retrieve=extend_schema(
        summary='Получить фоновый заказ',
        description=(
            'Возвращает полную информацию о фоновом заказе, включая тип, '
            'интервал вещания, плейлист и флаг бессрочности.'
        ),
        responses={
            HTTP_200_OK: BgOrderSerializer,
        } | DEFAULT_SCHEMA_RESPONSES,
    ),
)
@extend_schema(tags=['BG Orders'])
class BgOrderViewSet(NoDeleteViewSet):
    """
    ViewSet фоновых заказов.

    Типы фонового контента:

        0 — фоновая музыка;
        1 — фоновое видео;
        2 — фоновые изображения;
        3 — бегущая строка.

    Срочный заказ:

        is_permanent = False

        Используется только внутри указанного broadcast_interval.

    Бессрочный заказ:

        is_permanent = True

        Используется как резервный плейлист, если отсутствует активный
        срочный заказ соответствующего типа.
    """

    queryset = (
        BgOrder.objects
        .all()
        .select_related(
            'owner',
            'client',
            'client__brand',
            'client__typeOfPlace',
            'client__address__address__city__locality_type',
            'client__address__address__street__street_type',
            'playlist',
        )
    )

    serializer_class = BgOrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BgOrderFilter
    permission_classes = [StaffCUDAuthRetrieve]

    http_method_names = [
        'get',
        'post',
        'patch',
        'delete',
        'head',
        'options',
    ]

    def get_serializer_class(self):
        """
        Выбирает сериализатор фонового заказа.

        Returns:
            type[serializers.Serializer]:
                BgOrderListSerializer для списка;
                BgOrderSerializer для остальных действий.
        """
        if self.action == 'list':
            return BgOrderListSerializer

        return BgOrderSerializer

    def get_serializer(self, *args, **kwargs):
        """
        Создаёт сериализатор фонового заказа.

        Для списка входных объектов автоматически устанавливается many=True.
        """
        if isinstance(kwargs.get('data'), list):
            kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Создаёт фоновые заказы.

        Последовательность:

        1. Валидация данных.
        2. Создание отдельного заказа для каждого клиента.
        3. Приведение результата к плоскому списку.
        4. Создание Celery-задания после commit.
        5. Возврат заказа или списка заказов.

        Args:
            request:
                HTTP POST-запрос.

        Returns:
            Response:
                HTTP 201 и созданный заказ либо список заказов.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        saved_result = serializer.save(owner=request.user)
        orders = _normalize_created_orders(saved_result)

        if not orders:
            return Response(
                {
                    'detail': (
                        'Не создано ни одного фонового заказа. '
                        'Проверьте список clients.'
                    ),
                },
                status=HTTP_400_BAD_REQUEST,
            )

        order_ids = [
            str(order.id)
            for order in orders
        ]

        _enqueue_after_commit(
            create_bg_order_task,
            order_ids,
        )

        serializer_context = self.get_serializer_context()

        if len(orders) == 1:
            response_serializer = BgOrderSerializer(
                orders[0],
                context=serializer_context,
            )
        else:
            response_serializer = BgOrderListSerializer(
                orders,
                many=True,
                context=serializer_context,
            )

        return Response(
            response_serializer.data,
            status=HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """
        Частично обновляет фоновый заказ.

        Разрешённые поля:

        - name;
        - description;
        - playlist.

        При изменении плейлиста после commit создаётся
        update_bg_order_task.

        Args:
            request:
                HTTP PATCH-запрос.

        Returns:
            Response:
                Результат restricted_update().
        """
        error_message = (
            'Изменить можно только название, описание и '
            'плейлист. Лишние ключи: {keys}.'
        )

        updatable_fields = (
            'name',
            'description',
            'playlist',
        )

        kwargs.update(
            updatable_fields=updatable_fields,
            error_message=error_message,
        )

        response = restricted_update(
            self,
            request,
            *args,
            **kwargs,
        )

        update_succeeded = (
            HTTP_200_OK <= response.status_code < 300
        )

        if update_succeeded and 'playlist' in request.data:
            instance = self.get_object()

            _enqueue_after_commit(
                update_bg_order_task,
                order_id=str(instance.id),
            )

        return response

    @extend_schema(
        summary='Отменить фоновый заказ',
        description=(
            'Отменяет фоновый заказ и создаёт задание отмены для ПО.\n\n'
            'Отменить можно только заказ со статусом 0 или 1.'
        ),
        responses={
            HTTP_200_OK: DetailSerializer,
            HTTP_400_BAD_REQUEST: DetailSerializer,
        } | DEFAULT_SCHEMA_RESPONSES,
    )
    @action(detail=True, methods=['delete'])
    def cancel(self, request, pk=None):
        """
        Отменяет фоновый заказ.

        Args:
            request:
                HTTP DELETE-запрос.

            pk:
                UUID фонового заказа.

        Returns:
            Response:
                HTTP 200, если запрос принят;
                HTTP 400, если заказ уже завершён или отменён.
        """
        order = self.get_object()

        if order.status not in (0, 1):
            return Response(
                {
                    'detail': (
                        'Отменить можно только ожидающий '
                        'или находящийся в эфире заказ.'
                    ),
                },
                status=HTTP_400_BAD_REQUEST,
            )

        _enqueue_after_commit(
            cancel_bg_order_task,
            str(order.id),
        )

        return Response(
            {
                'message': (
                    'Запрос на отмену фонового заказа принят.'
                ),
            },
            status=HTTP_200_OK,
        )