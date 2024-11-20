from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.response import Response

from tasks.filters import TaskFilter
from tasks.serializers import TaskSerializer, TaskListSerializer
from tasks.models import Task, STATUSES
from users.permissions import OnlyStaffCRUD


class TaskViewSet(viewsets.ModelViewSet):
    """Работа с репликациями."""

    queryset = Task.objects.all().select_related('owner', 'client')
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter
    permission_classes = [OnlyStaffCRUD]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.perform_destroy(instance)
        return Response(data=data, status=400 if data else 204)

    def perform_destroy(self, instance):
        if instance.status == 0:
            instance.status = 3
            instance.save()
            return None
        else:
            return (
                'Нельзя отменить репликацию со статусом '
                f'{STATUSES[instance.status]}'
            )

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
