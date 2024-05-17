from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from tasks.filters import TaskFilter
from tasks.serializers import TaskSerializer, TaskListSerializer
from tasks.models import Task
from users.permissions import AuthAndOnlySuperUserDelete


class TaskViewSet(viewsets.ModelViewSet):
    """Работа с репликациями."""

    queryset = Task.objects.all().select_related(
        'owner', 'client'
    ).order_by('-created')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = TaskListSerializer
        else:
            serializer = TaskSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)
