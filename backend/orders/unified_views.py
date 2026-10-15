"""REST-методы единых заказов фона и рекламы."""

from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from api.constants import DEFAULT_SCHEMA_RESPONSES, DetailSerializer
from docs import integration_documentation as integration_docs
from orders.filters import UnifiedOrderFilter
from files.models import Playlist
from orders.models import Order
from orders.services.order_audio_images import (
    get_order_audio_images,
    validate_order_audio_images,
    with_order_audio_images,
)
from orders.services.unified_order_delivery import enqueue_cancellation, enqueue_order
from orders.services.unified_order_input import validate_prepared_orders
from orders.unified_serializers import (
    UnifiedOrderResendSerializer,
    UnifiedOrderResponseSerializer,
    UnifiedOrderSerializer,
    public_order_errors,
)
from users.permissions import StaffCUDAuthRetrieve


AD_EXAMPLE = {
    "name": "Осенняя рекламная кампания",
    "description": "Аудиоролики с привязанными картинками",
    "type": "ad",
    "clients": ["5778e050-454d-4e5e-ae0f-bb584979552c"],
    "playlist": "3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c",
    "broadcast_interval": {
        "lower": "2026-09-25 09:00:00",
        "upper": "2026-10-01 21:00:00",
    },
    "broadcast_type": 0,
    "parameters": {"times_in_hour": 4},
    "suppress_background_audio": False,
    "suppress_background_visual": False,
}

BACKGROUND_EXAMPLE = {
    "name": "Музыка торгового зала",
    "type": "bg",
    "clients": ["5778e050-454d-4e5e-ae0f-bb584979552c"],
    "playlist": "3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c",
    "is_permanent": True,
    "parameters": {},
}

AUDIO_IMAGES_EXAMPLE = {
    **AD_EXAMPLE,
    "name": "Аудиореклама с картинками этого заказа",
    "audio_images": {
        "11111111-1111-4111-8111-111111111111": [
            "22222222-2222-4222-8222-222222222222",
            "66666666-6666-4666-8666-666666666666",
        ],
    },
}

HOURLY_EXAMPLE = {
    **AD_EXAMPLE,
    "parameters": {"times_in_hour": 8},
}
WEEKDAY_AD_EXAMPLE = {
    **AD_EXAMPLE,
    "name": "Реклама по понедельникам, средам и пятницам",
    "parameters": {"times_in_hour": 4, "weekdays": [0, 2, 4]},
}
WEEKDAY_BACKGROUND_EXAMPLE = {
    **BACKGROUND_EXAMPLE,
    "name": "Временный фон по будням поверх резервного",
    "is_permanent": False,
    "broadcast_interval": {
        "lower": "2026-10-13 09:00:00",
        "upper": "2026-11-01 18:00:00",
    },
    "parameters": {"weekdays": [0, 1, 2, 3, 4], "weight": 70},
}
CONTINUOUS_EXAMPLE = {
    **AD_EXAMPLE,
    "name": "Непрерывная реклама без звука",
    "broadcast_type": 7,
    "parameters": {"weight": 70, "audio_muted": True, "image_duration_seconds": 12},
    "suppress_background_audio": False,
    "suppress_background_visual": True,
}
OPEN_OFFSET_EXAMPLE = {**AD_EXAMPLE, "broadcast_type": 1, "parameters": {"times_in_hour": 4, "timedelta": "00:30:00"}}
CLOSE_OFFSET_EXAMPLE = {**AD_EXAMPLE, "broadcast_type": 2, "parameters": {"times_in_hour": 4, "timedelta": "00:15:00"}}
FIXED_TIME_EXAMPLE = {**AD_EXAMPLE, "broadcast_type": 3, "parameters": {"times_in_hour": 4, "start_time": "10:00:00", "end_time": "18:00:00"}}
OPEN_TO_FIXED_EXAMPLE = {**AD_EXAMPLE, "broadcast_type": 4, "parameters": {"times_in_hour": 4, "end_time": "14:00:00"}}
FIXED_TO_CLOSE_EXAMPLE = {**AD_EXAMPLE, "broadcast_type": 5, "parameters": {"times_in_hour": 4, "start_time": "16:00:00"}}
START_TO_CLOSE_EXAMPLE = {**AD_EXAMPLE, "broadcast_type": 5, "parameters": {"times_in_hour": 4, "start_time": "09:07:30"}}
EVENT_EXAMPLE = {**AD_EXAMPLE, "broadcast_type": 6, "parameters": {"times_in_hour": 1, "event": "door_open", "active_ad": "wait_until_end"}}
BATCH_EXAMPLE = {
    **AD_EXAMPLE,
    "clients": [
        "5778e050-454d-4e5e-ae0f-bb584979552c",
        "5778e050-454d-4e5e-ae0f-bb584979552d",
    ],
}
CREATED_AD_EXAMPLE = {
    **AD_EXAMPLE,
    "clients": [{"id": AD_EXAMPLE["clients"][0], "name": "Точка на Ленина, 10"}],
    "id": "00000000-0000-0000-0000-000000000101",
    "description": AD_EXAMPLE["description"], "is_permanent": False,
    "status": 0, "owner": {"id": "00000000-0000-0000-0000-000000000102", "full_name": "Иванов Иван"},
    "created": "2026-09-30 13:04:00",
}
CREATED_BACKGROUND_EXAMPLE = {
    **BACKGROUND_EXAMPLE,
    "clients": [{"id": BACKGROUND_EXAMPLE["clients"][0], "name": "Точка на Ленина, 10"}],
    "id": "00000000-0000-0000-0000-000000000103",
    "description": None, "broadcast_interval": {"lower": None, "upper": None},
    "order_type": 0,
    "suppress_background_audio": False, "suppress_background_visual": False,
    "status": 0, "owner": {"id": "00000000-0000-0000-0000-000000000102", "full_name": "Иванов Иван"},
    "created": "2026-09-30 13:04:00",
}


class UnifiedOrderSchema(AutoSchema):
    """Создание возвращает массив без пагинации; список GET остаётся постраничным."""

    def _get_paginator(self):
        if getattr(self.view, "action", None) == "create":
            return None
        return super()._get_paginator()


@extend_schema_view(
    list=extend_schema(
        summary="Список единых заказов эфира",
        description=integration_docs.BROADCAST_ORDER_LIST_DESCRIPTION,
        responses={200: UnifiedOrderResponseSerializer(many=True)} | DEFAULT_SCHEMA_RESPONSES,
    ),
    retrieve=extend_schema(
        summary="Получить единый заказ эфира",
        description=integration_docs.BROADCAST_ORDER_RETRIEVE_DESCRIPTION,
        responses={200: UnifiedOrderResponseSerializer} | DEFAULT_SCHEMA_RESPONSES,
    ),
    create=extend_schema(
        summary="Создать единый заказ эфира",
        description=(
            integration_docs.BROADCAST_ORDER_CREATE_DESCRIPTION
            + "\n\nПередайте массив clients с UUID одной или нескольких номенклатур. "
              "Ответ всегда содержит массив заказов, включая запрос из одного UUID, "
              "в том же порядке, что и запрос. Сначала проверяется весь пакет; при любой "
              "ошибке заказы и команды не создаются."
        ),
        request=UnifiedOrderSerializer,
        examples=[
            OpenApiExample("Рекламные выходы", value=AD_EXAMPLE, request_only=True),
            OpenApiExample("Аудио с картинками заказа", value=AUDIO_IMAGES_EXAMPLE, request_only=True),
            OpenApiExample("Один заказ для нескольких точек", value=BATCH_EXAMPLE, request_only=True),
            OpenApiExample("Реклама в выбранные дни недели", value=WEEKDAY_AD_EXAMPLE, request_only=True),
            OpenApiExample("Временный фон по будням", value=WEEKDAY_BACKGROUND_EXAMPLE, request_only=True),
            OpenApiExample("Восемь выходов в час", value=HOURLY_EXAMPLE, request_only=True),
            OpenApiExample("Непрерывная реклама, музыка остаётся", value=CONTINUOUS_EXAMPLE, request_only=True),
            OpenApiExample("Через 30 минут после открытия", value=OPEN_OFFSET_EXAMPLE, request_only=True),
            OpenApiExample("За 15 минут до закрытия", value=CLOSE_OFFSET_EXAMPLE, request_only=True),
            OpenApiExample("В фиксированном интервале", value=FIXED_TIME_EXAMPLE, request_only=True),
            OpenApiExample("От открытия до 14:00", value=OPEN_TO_FIXED_EXAMPLE, request_only=True),
            OpenApiExample("С 16:00 до закрытия", value=FIXED_TO_CLOSE_EXAMPLE, request_only=True),
            OpenApiExample("Реклама с указанного времени", value=START_TO_CLOSE_EXAMPLE, request_only=True),
            OpenApiExample("По событию Player", value=EVENT_EXAMPLE, request_only=True),
            OpenApiExample("Бессрочный музыкальный фон", value=BACKGROUND_EXAMPLE, request_only=True),
            OpenApiExample("Созданный рекламный заказ", value=CREATED_AD_EXAMPLE, response_only=True, status_codes=["201"]),
            OpenApiExample("Созданный бессрочный фон", value=CREATED_BACKGROUND_EXAMPLE, response_only=True, status_codes=["201"]),
        ],
        responses={
            201: OpenApiResponse(
                response=UnifiedOrderResponseSerializer(many=True),
                description="Массив созданных заказов в порядке UUID в clients.",
            )
        } | DEFAULT_SCHEMA_RESPONSES,
    ),
    partial_update=extend_schema(
        summary="Изменить единый заказ и отправить новую редакцию Player",
        description=integration_docs.BROADCAST_ORDER_UPDATE_DESCRIPTION,
        request=UnifiedOrderSerializer,
        examples=[
            OpenApiExample(
                "Изменить только картинки, сохранив расписание",
                value={"audio_images": AUDIO_IMAGES_EXAMPLE["audio_images"]},
                request_only=True,
            ),
            OpenApiExample("Убрать сопровождение аудио", value={"audio_images": {}}, request_only=True),
        ],
        responses={200: UnifiedOrderResponseSerializer} | DEFAULT_SCHEMA_RESPONSES,
    ),
)
@extend_schema(tags=["Заказы эфира v2"])
class UnifiedOrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Заказы физически не удаляем: для прекращения эфира используется отмена."""

    queryset = Order.objects.select_related("owner", "nomenclature", "playlist").prefetch_related(
        "playlist__items__file", "playlist__files",
    )
    serializer_class = UnifiedOrderSerializer
    schema = UnifiedOrderSchema()
    permission_classes = [StaffCUDAuthRetrieve]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UnifiedOrderFilter
    http_method_names = ["get", "post", "patch", "head", "options"]

    def create(self, request, *args, **kwargs):
        """Проверяем все точки, затем атомарно создаём заказы и команды."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attributes = dict(serializer.validated_data)
        targets = attributes.pop("clients")
        orders = [
            Order(owner=request.user, nomenclature=target, **attributes)
            for target in targets
        ]
        try:
            validate_prepared_orders(orders)
        except ValidationError as exc:
            raise ValidationError(public_order_errors(exc.detail)) from exc

        with transaction.atomic():
            self._validate_new_order_media(orders)
            for order in orders:
                order.save(force_insert=True)
                self._enqueue(order)

        by_id = {
            order.pk: order
            for order in self.get_queryset().filter(pk__in=[order.pk for order in orders])
        }
        ordered = [by_id[order.pk] for order in orders]
        response_serializer = UnifiedOrderResponseSerializer(
            ordered,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _validate_new_order_media(orders) -> None:
        """Повторно проверяем привязки внутри транзакции перед созданием заказов.

        Между проверкой запроса и записью файлы могли измениться. Блокируем
        плейлисты в стабильном порядке, затем проверяем и блокируем картинки.
        """
        playlist_ids = sorted({order.playlist_id for order in orders}, key=str)
        playlists = {
            playlist.pk: playlist
            for playlist in (
                Playlist.objects.select_for_update(no_key=True)
                .filter(pk__in=playlist_ids)
                .order_by("pk")
            )
        }
        if len(playlists) != len(playlist_ids):
            raise ValidationError({"playlist": "Выбранный плейлист больше не существует."})

        for order in orders:
            playlist = playlists[order.playlist_id]
            order.playlist = playlist
            mapping = get_order_audio_images(order)
            if not mapping:
                continue
            try:
                mapping = validate_order_audio_images(
                    mapping,
                    playlist=playlist,
                    placement=order.placement,
                )
            except DjangoValidationError as exc:
                raise ValidationError(exc.message_dict) from exc
            order.parameters = with_order_audio_images(order.parameters, mapping)

    @staticmethod
    def _enqueue(order, *, cancel=False):
        try:
            return enqueue_cancellation(order) if cancel else enqueue_order(order)
        except DjangoValidationError as exc:
            raise ValidationError({"detail": exc.messages}) from exc

    def perform_update(self, serializer):
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=serializer.instance.pk)
            if not order.is_active:
                raise ValidationError("Отменённый заказ нельзя редактировать; создайте новый заказ.")
            # После блокировки проверяем PATCH по актуальным настройкам,
            # чтобы не затереть параллельное изменение картинок заказа.
            locked_serializer = self.get_serializer(
                order, data=self.request.data, partial=True
            )
            locked_serializer.is_valid(raise_exception=True)
            order = locked_serializer.save(revision=order.revision + 1)
            serializer.instance = order
            self._enqueue(order)

    @extend_schema(
        summary="Отменить единый заказ эфира",
        description=integration_docs.BROADCAST_ORDER_CANCEL_DESCRIPTION,
        responses={200: OpenApiResponse(response=DetailSerializer)} | DEFAULT_SCHEMA_RESPONSES,
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        with transaction.atomic():
            order = get_object_or_404(self.get_queryset().select_for_update(of=("self",)), pk=pk)
            self.check_object_permissions(request, order)
            if not order.is_active:
                return Response({"detail": "Отмена уже запрошена; состояние смотрите в карточке заказа."})
            if order.status not in (0, 1, 4):
                return Response({"detail": "Отменить можно только ожидающий или активный заказ."}, status=status.HTTP_400_BAD_REQUEST)
            order.is_active = False
            order.revision += 1
            order.save(update_fields=("is_active", "revision"))
            self._enqueue(order, cancel=True)
        return Response({"detail": "Отмена запрошена; ожидается подтверждение Player."})

    @extend_schema(
        summary="Повторно отправить несколько заказов Player",
        description=integration_docs.BROADCAST_ORDER_RESEND_DESCRIPTION,
        request=UnifiedOrderResendSerializer,
        responses={200: DetailSerializer} | DEFAULT_SCHEMA_RESPONSES,
        examples=[
            OpenApiExample(
                "Повторная отправка двух заказов",
                value={
                    "order_ids": [
                        "00000000-0000-0000-0000-000000000101",
                        "00000000-0000-0000-0000-000000000102",
                    ]
                },
                request_only=True,
            )
        ],
    )
    @action(detail=False, methods=["post"], url_path="resend")
    def resend(self, request):
        payload = UnifiedOrderResendSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        requested_ids = payload.validated_data["order_ids"]
        orders = list(self.get_queryset().filter(pk__in=requested_ids, status__in=(0, 1), is_active=True))
        found_ids = {order.pk for order in orders}
        unavailable_ids = [str(order_id) for order_id in requested_ids if order_id not in found_ids]
        if unavailable_ids:
            return Response(
                {
                    "detail": "Можно отправить только ожидающие или активные заказы.",
                    "unavailable_order_ids": unavailable_ids,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            for order_id in requested_ids:
                order = Order.objects.select_for_update(of=("self",)).select_related("owner", "nomenclature", "playlist").get(pk=order_id)
                self.check_object_permissions(request, order)
                if not order.is_active or order.status not in (0, 1):
                    raise ValidationError("Состояние заказа изменилось; повторите запрос.")
                self._enqueue(order)
        return Response({"detail": "Заказы поставлены в очередь Player.", "count": len(requested_ids)})
