from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from orders.filters import AdOrderFilter, BgOrderFilter
from orders.serializers import (
    AdOrderSerializer,
    AdOrderListSerializer,
    BgOrderSerializer,
    BgOrderListSerializer
)

from orders.models import AdOrder, BgOrder
from tasks.models import Task


class AdOrderViewSet(viewsets.ModelViewSet):
    """Работа с заказами."""

    queryset = AdOrder.objects.all().select_related('owner', 'group', 'file')
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdOrderFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        order = serializer.save(owner=self.request.user)
        clients = order.group.clients.all()
        task_list = (
            Task(
                owner=self.request.user,
                client=client,
                type=4,
                parameters={
                    'order_parameters': order.parameters,
                    'broadcast_type': order.broadcast_type,
                    'broadcast_interval': order.broadcast_interval,
                    'file': order.file,
                    'slides': [
                        {'id': str(slide.id),
                         'name': slide.name} for slide in order.slides.all()
                    ] if order.slides.exists() else None
                }
            ) for client in clients
        )
        Task.objects.bulk_create(task_list)

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
        'owner', 'client', 'playlist'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = BgOrderFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        order = serializer.save(owner=self.request.user)
        task = Task.objects.create(
            owner=self.request.user,
            client=order.client,
            type=order.order_type,
            parameters={
                'type': order.order_type,
                'playlist': order.playlist.name,
                'broadcast_interval': order.broadcast_interval
            }
        )
        task.save()

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
