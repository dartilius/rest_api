from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from tasks.serializers import TaskSerializer
from tasks.models import Task
from users.permissions import AuthAndOnlySuperUserDelete


class TaskViewSet(viewsets.ModelViewSet):
    """Работа с репликациями."""

    queryset = Task.objects.all().select_related('owner')
    serializer_class = TaskSerializer
    pagination_class = LimitOffsetPagination
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        task = serializer.save(owner=self.request.user)
