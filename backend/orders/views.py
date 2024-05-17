from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from files.models import File, Playlist
from orders.filters import AdOrderFilter, BgOrderFilter
from orders.serializers import (
    AdOrderSerializer,
    AdOrderListSerializer,
    BgOrderSerializer,
    BgOrderListSerializer
)

from orders.models import AdOrder, BgOrder
from tasks.models import Task, Type

from users.permissions import AuthAndOnlySuperUserDelete


class AdOrderViewSet(viewsets.ModelViewSet):
    """Работа с заказами."""

    queryset = AdOrder.objects.all().select_related('owner', 'group', 'file')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = AdOrderFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        order = serializer.save(owner=self.request.user)
        clients = order.group.clients.all()
        task_list = (
            Task(
                owner=self.request.user,
                client=client,
                type=0,
                parameters={
                    'parameters': serializer.data[
                        'adorder__parameters'
                    ],
                    'broadcast_type': serializer.data[
                        'adorder__broadcast_type'
                    ],
                    'files': File.objects.filter(
                        serializer.data['file']
                    )
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
        'owner',
        'client',
        'playlist'
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = BgOrderFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        order = serializer.save(owner=self.request.user)
        client = order.client.all()
        Task.objects.create(
            owner=self.request.user,
            client=client,
            type=Type.objects.get(order_type=serializer.data['order_type']),
            parameters={
                'playlist': Playlist.objects.filter(
                    serializer.data['playlist']
                )
            }
        )

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
