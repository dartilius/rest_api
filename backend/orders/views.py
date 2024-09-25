from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from orders.filters import AdOrderFilter, BgOrderFilter
from orders.serializers import (
    AdOrderSerializer,
    AdOrderListSerializer,
    BgOrderSerializer,
    BgOrderListSerializer
)
from orders.models import AdOrder, BgOrder
from tasks.tasks import (
    create_ad_order_task,
    update_ad_order_task,
    cancel_ad_order_task,
    create_bg_order_task,
    update_bg_order_task,
    cancel_bg_order_task
)


class AdOrderViewSet(viewsets.ModelViewSet):
    """Работа с заказами."""

    queryset = AdOrder.objects.all().select_related('owner', 'group', 'file')
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdOrderFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        orders = serializer.save(owner=self.request.user)
        orders_ids = list(order.id for order in orders)
        create_ad_order_task.delay(orders_ids)

    def perform_update(self, serializer):
        pass
        # data = serializer.data
        # updated_data = {k: v for k, v in data.items() if k != 'id'}
        # orders = serializer.save(update_fields=[*updated_data.keys()])
        # orders_ids = [order.id for order in orders]
        # update_ad_order_task.delay(orders_ids, updated_data)

    def perform_destroy(self, instance):
        cancel_ad_order_task.delay([instance.id])

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


class BgOrderViewSet(viewsets.ModelViewSet):
    """Работа с заказами."""

    queryset = BgOrder.objects.all().select_related(
        'owner', 'group', 'playlist'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = BgOrderFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        orders = serializer.save(owner=self.request.user)
        orders_ids = list(order.id for order in orders)
        create_bg_order_task.delay(orders_ids)

    def perform_update(self, serializer):
        pass
        # data = serializer.data
        # updated_data = {k: v for k, v in data.items() if k != 'id'}
        # order = serializer.save(update_fields=[*updated_data.keys()])
        # update_bg_order_task.delay(order.id, updated_data)

    def perform_destroy(self, instance):
        cancel_bg_order_task.delay([instance.id])

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
