from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from api.constants import restricted_update
from orders.filters import AdOrderFilter, BgOrderFilter
from orders.serializers import (
    AdOrderSerializer,
    AdOrderListSerializer,
    BgOrderSerializer,
    BgOrderListSerializer
)
from orders.models import AdOrder, BgOrder
from orders.tasks import (
    create_ad_order_task,
    cancel_ad_order_task,
    create_bg_order_task,
    cancel_bg_order_task,
)
from users.permissions import StaffCUDAuthRetrieve


class NoDeleteViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """Вьюсет без поддержки метода DELETE."""


class AdOrderViewSet(NoDeleteViewSet):
    """Работа с рекламными заказами."""

    queryset = AdOrder.objects.all().select_related(
        'owner', 'client', 'playlist'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdOrderFilter
    permission_classes = [StaffCUDAuthRetrieve]

    def perform_create(self, serializer):
        """
        Создание заказов.

        0. Получаем данные из сериализатора.
        1. Сохраняем заказы, владельца берём из запроса.
        2. Собираем айди заказов.
        3. Передаём список айди в целери для создания репликаций в фоне.
        """
        # 0
        serializer.is_valid(raise_exception=True)
        # 1
        orders_list = serializer.save(owner=self.request.user)
        orders_ids = []
        # 2
        for orders in orders_list:
            orders_ids.append(
                [str(order.id) for order in orders]
                if len(orders) > 1 else str(orders[0].id)
            )
        # 3
        create_ad_order_task.delay(orders_ids)

    def update(self, request, *args, **kwargs):
        error_message = (
            'Изменить можно только название, описание, '
            'плейлист и слайды. Лишние ключи: {keys}.'
        )
        updatable_fields = (
            'name',
            'description',
            'playlist',
            'slides'
        )
        kwargs.update(updatable_fields=updatable_fields,
                      error_message=error_message)
        response = restricted_update(self, request, *args, **kwargs)
        return response

    @action(detail=True, methods=['DELETE'])
    def cancel(self, request, pk):
        """Отмена заказа."""
        cancel_ad_order_task.delay(str(pk))
        result_text = f'Запрос на отмену заказа принят.'
        return Response(data=result_text, status=HTTP_200_OK)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = AdOrderListSerializer
        else:
            serializer = AdOrderSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)


class BgOrderViewSet(NoDeleteViewSet):
    """Работа с фоновыми заказами."""

    queryset = BgOrder.objects.all().select_related(
        'owner', 'client', 'playlist'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = BgOrderFilter
    permission_classes = [StaffCUDAuthRetrieve]

    def perform_create(self, serializer):
        """
        Создание заказов.

        0. Получаем данные из сериализатора.
        1. Сохраняем заказы, владельца берём из запроса.
        2. Собираем айди заказов.
        3. Передаём список айди в целери для создания репликаций в фоне.
        """
        # 0
        serializer.is_valid(raise_exception=True)
        # 1
        orders_list = serializer.save(owner=self.request.user)
        orders_ids = []
        # 2
        for orders in orders_list:
            orders_ids.append(
                [str(order.id) for order in orders]
                if len(orders) > 1 else str(orders[0].id)
            )
        # 3
        create_bg_order_task.delay(orders_ids)

    def update(self, request, *args, **kwargs):
        error_message = (
            'Изменить можно только название, описание и '
            'плейлист. Лишние ключи: {keys}.'
        )
        updatable_fields = (
            'name',
            'description',
            'playlist'
        )
        kwargs.update(updatable_fields=updatable_fields,
                      error_message=error_message)
        response = restricted_update(self, request, *args, **kwargs)
        return response

    @action(detail=True, methods=['DELETE'])
    def cancel(self, request, pk):
        """Отмена заказа."""
        cancel_bg_order_task.delay(str(pk))
        result_text = f'Запрос на отмену заказа принят.'
        return Response(data=result_text, status=HTTP_200_OK)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = BgOrderListSerializer
        else:
            serializer = BgOrderSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)
