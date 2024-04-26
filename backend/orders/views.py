from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from files.models import PlaylistFiles
from orders.serializers import OrderSerializer

from orders.models import Order
from tasks.models import Task, Type

from users.permissions import AuthAndOnlySuperUserDelete


class OrderViewSet(viewsets.ModelViewSet):
    """Работа с заказами."""

    queryset = Order.objects.all().select_related(
            'owner'
        ).select_related('playlist').select_related('group')
    serializer_class = OrderSerializer
    pagination_class = LimitOffsetPagination
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        order = serializer.save(owner=self.request.user)
        clients = order.group.clients.all()
        task_list = (
            Task(
                owner=self.request.user,
                client=client,
                type=Type.objects.get(order_type=serializer.data['type']),
                parameters={
                    'parameters': serializer.data[
                        'playlist__settings__parameters'
                    ],
                    'broadcast_type': serializer.data[
                        'playlist__settings__broadcast_type'
                    ],
                    'files': PlaylistFiles.objects.filter(
                        serializer.data['playlist']
                    )
                }
            ) for client in clients
        )
        Task.objects.bulk_create(task_list)
