from django.db.models import Q
from django_filters import CharFilter, DateFromToRangeFilter
from django_filters.rest_framework import FilterSet

from tasks.models import Task


class TaskFilter(FilterSet):
    """Фильтрация номенклатур."""

    owner = CharFilter(method='filter_by_owner_name')
    id = CharFilter(field_name='id', lookup_expr='exact')
    type = CharFilter(field_name='type', lookup_expr='iexact')
    status = CharFilter(field_name='status', lookup_expr='exact')
    client = CharFilter(
        field_name='client__name',
        lookup_expr='iexact',
        label='Целевая рабочая станция'
    )
    created = DateFromToRangeFilter(field_name='created')

    class Meta:
        model = Task
        fields = ('id', 'owner', 'client', 'type', 'status', 'created')

    def filter_by_owner_name(self, queryset, name, value):
        if len(value.split()) == 2:
            first_name, last_name = value.split()
            return queryset.filter(
                (Q(owner__last_name__icontains=last_name) &
                 Q(owner__first_name__icontains=first_name)) |
                (Q(owner__last_name__icontains=first_name) &
                 Q(owner__first_name__icontains=last_name))
            )
        elif len(value.split()) == 1:
            return queryset.filter(
                Q(owner__last_name__icontains=value) |
                Q(owner__first_name__icontains=value)
            )
