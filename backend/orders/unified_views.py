"""Documented REST endpoints for unified broadcast orders."""

from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from api.constants import DEFAULT_SCHEMA_RESPONSES, DetailSerializer
from docs import integration_documentation as integration_docs
from orders.filters import UnifiedOrderFilter
from orders.models import Order
from orders.services.order_air_state import with_playback_evidence
from orders.services.order_progress import with_order_progress
from orders.services.unified_order_delivery import enqueue_cancellation, enqueue_order
from orders.unified_serializers import UnifiedOrderResendSerializer, UnifiedOrderSerializer
from users.permissions import StaffCUDAuthRetrieve


AD_EXAMPLE = {
    "name": "Осенняя рекламная кампания",
    "description": "Аудиоролики с привязанными картинками",
    "placement": "advertising",
    "playback_policy": "workday",
    "nomenclature": "5778e050-454d-4e5e-ae0f-bb584979552c",
    "playlist": "3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c",
    "starts_at": "2026-09-25 09:00:00",
    "ends_at": "2026-10-01 21:00:00",
    "parameters": {"times_in_hour": 4},
    "suppress_background_audio": False,
    "suppress_background_visual": False,
}

BACKGROUND_EXAMPLE = {
    "name": "Музыка торгового зала",
    "placement": "background",
    "playback_policy": "workday",
    "nomenclature": "5778e050-454d-4e5e-ae0f-bb584979552c",
    "playlist": "3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c",
    "is_permanent": True,
    "parameters": {},
}

HOURLY_EXAMPLE = {**AD_EXAMPLE, "playback_policy": "hourly_slots", "parameters": {"times_in_hour": 8}}
CONTINUOUS_EXAMPLE = {
    **AD_EXAMPLE,
    "name": "Непрерывная реклама без звука",
    "playback_policy": "continuous",
    "parameters": {"weight": 70, "audio_muted": True, "image_duration_seconds": 12},
    "suppress_background_audio": False,
    "suppress_background_visual": True,
}
OPEN_OFFSET_EXAMPLE = {**AD_EXAMPLE, "playback_policy": "open_offset", "parameters": {"times_in_hour": 4, "timedelta": "00:30:00"}}
CLOSE_OFFSET_EXAMPLE = {**AD_EXAMPLE, "playback_policy": "close_offset", "parameters": {"times_in_hour": 4, "timedelta": "00:15:00"}}
FIXED_TIME_EXAMPLE = {**AD_EXAMPLE, "playback_policy": "fixed_time", "parameters": {"times_in_hour": 4, "start_time": "10:00:00", "end_time": "18:00:00"}}
OPEN_TO_FIXED_EXAMPLE = {**AD_EXAMPLE, "playback_policy": "open_to_fixed", "parameters": {"times_in_hour": 4, "end_time": "14:00:00"}}
FIXED_TO_CLOSE_EXAMPLE = {**AD_EXAMPLE, "playback_policy": "fixed_to_close", "parameters": {"times_in_hour": 4, "start_time": "16:00:00"}}
START_TO_CLOSE_EXAMPLE = {**AD_EXAMPLE, "playback_policy": "start_to_close", "parameters": {"times_in_hour": 4, "start_time": "09:07:30"}}
EVENT_EXAMPLE = {**AD_EXAMPLE, "playback_policy": "event", "parameters": {"times_in_hour": 1, "event": "door_open", "active_ad": "wait_until_end"}}

CREATED_AD_EXAMPLE = {
    **AD_EXAMPLE, "id": "00000000-0000-0000-0000-000000000101",
    "description": AD_EXAMPLE["description"], "is_permanent": False,
    "status": 0, "revision": 1, "owner": "00000000-0000-0000-0000-000000000102",
    "created": "2026-09-30 13:04:00", "delivery": None,
}
CREATED_BACKGROUND_EXAMPLE = {
    **BACKGROUND_EXAMPLE, "id": "00000000-0000-0000-0000-000000000103",
    "description": None, "starts_at": None, "ends_at": None,
    "suppress_background_audio": False, "suppress_background_visual": False,
    "status": 0, "revision": 1, "owner": "00000000-0000-0000-0000-000000000102",
    "created": "2026-09-30 13:04:00", "delivery": None,
}


@extend_schema_view(
    list=extend_schema(summary="Список единых заказов эфира", description=integration_docs.BROADCAST_ORDER_LIST_DESCRIPTION),
    retrieve=extend_schema(summary="Получить единый заказ эфира", description=integration_docs.BROADCAST_ORDER_RETRIEVE_DESCRIPTION),
    create=extend_schema(
        summary="Создать единый заказ эфира",
        description=integration_docs.BROADCAST_ORDER_CREATE_DESCRIPTION,
        request=UnifiedOrderSerializer,
        examples=[
            OpenApiExample("Рекламные выходы", value=AD_EXAMPLE, request_only=True),
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
        responses={201: UnifiedOrderSerializer} | DEFAULT_SCHEMA_RESPONSES,
    ),
    partial_update=extend_schema(
        summary="Изменить единый заказ и отправить новую редакцию Player",
        description=integration_docs.BROADCAST_ORDER_UPDATE_DESCRIPTION,
        request=UnifiedOrderSerializer,
        responses={200: UnifiedOrderSerializer} | DEFAULT_SCHEMA_RESPONSES,
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
    """CRUD without physical deletion; use the cancel action instead."""

    queryset = with_order_progress(with_playback_evidence(Order.objects.select_related("owner", "nomenclature", "playlist", "station_state")))
    serializer_class = UnifiedOrderSerializer
    permission_classes = [StaffCUDAuthRetrieve]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UnifiedOrderFilter
    http_method_names = ["get", "post", "patch", "head", "options"]

    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save(owner=self.request.user)
            self._enqueue(order)

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
            serializer.instance = order
            order = serializer.save(revision=order.revision + 1)
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
