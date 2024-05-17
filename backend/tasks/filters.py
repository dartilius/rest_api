from django.db.models import Q
from django_filters import CharFilter
from django_filters.rest_framework import FilterSet

from tasks.models import Task


class TaskFilter(FilterSet):
    """Фильтрация номенклатур."""

    owner = CharFilter(method='filter_by_owner_name')

    class Meta:
        model = Task
        fields = {
            'id': ['exact'],
            'type': ['exact'],
            'status': ['exact'],
            'client__name': ['icontains'],
            'created': ['exact', 'gte', 'lte', 'range']
        }

    def filter_by_owner_name(self, queryset, name, value):
        return queryset.filter(
            Q(owner__last_name__icontains=value) | Q(owner__first_name__icontains=value)
        )
