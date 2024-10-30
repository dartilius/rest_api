from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

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


class NoDeleteViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """Вьюсет без предустановленного метода DELETE."""
    pass


class AdOrderViewSet(NoDeleteViewSet):
    """Работа с рекламными заказами."""

    queryset = AdOrder.objects.all().select_related(
        'owner', 'client', 'playlist'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdOrderFilter

    def perform_create(self, serializer):
        """
        Создание заказов.

        0. Получаем данные из сериализатора.
        1. Сохраняем заказы, владельца берём из запроса.
        2. Собираем айди заказов.
        3. Передаём список айди в целери для создания репликаций в фоне.
        """
        orders_list = serializer.save(owner=self.request.user)
        for orders in orders_list:
            orders_ids = [order.id for order in orders]
            create_ad_order_task.delay(orders_ids)

    @action(detail=True, methods=['DELETE'])
    def cancel(self, request, pk):
        """Отмена заказа."""
        cancel_ad_order_task.delay([str(pk)])
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

    def perform_create(self, serializer):
        """
        Создание заказов.

        0. Получаем данные из сериализатора.
        1. Сохраняем заказы, владельца берём из запроса.
        2. Собираем айди заказов.
        3. Передаём список айди в целери для создания репликаций в фоне.
        """
        orders_list = serializer.save(owner=self.request.user)
        for orders in orders_list:
            orders_ids = [order.id for order in orders]
            create_bg_order_task.delay(orders_ids)

    def perform_update(self, serializer):
        """Запрет на обновление типа заказа."""
        if 'order_type' in serializer.data:
            return Response(data='Нельзя менять тип заказа.', status=400)
        super().perform_update(serializer)

    @action(detail=True, methods=['DELETE'])
    def cancel(self, request, pk):
        """Отмена заказа."""
        cancel_bg_order_task.delay([str(pk)])
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
