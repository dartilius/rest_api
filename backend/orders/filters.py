from django.db.models import Q
from django_filters import CharFilter
from django_filters.rest_framework import FilterSet

from orders.models import AdOrder, BgOrder


class AdOrderFilter(FilterSet):
    """Фильтрация номенклатур."""

    owner = CharFilter(method='filter_by_owner_name')

    class Meta:
        model = AdOrder
        fields = {
            'name': ['icontains'],
            'broadcast_type': ['exact'],
            'id': ['exact'],
            'group__name': ['icontains']
        }

    def filter_by_owner_name(self, queryset, name, value):
        return queryset.filter(
            Q(owner__last_name__icontains=value) | Q(owner__first_name__icontains=value)
        )


class BgOrderFilter(FilterSet):
    """Фильтрация номенклатур."""

    owner = CharFilter(method='filter_by_owner_name')

    class Meta:
        model = BgOrder
        fields = {
            'name': ['icontains'],
            'id': ['exact'],
            'client__name': ['icontains'],
            'order_type': ['exact']
        }

    def filter_by_owner_name(self, queryset, name, value):
        return queryset.filter(
            Q(owner__last_name__icontains=value) | Q(owner__first_name__icontains=value)
        )
