from django_filters.rest_framework import FilterSet

from orders.models import AdOrder, BgOrder


class AdOrderFilter(FilterSet):
    """Фильтрация номенклатур."""

    class Meta:
        model = AdOrder
        fields = {
            'name': ['icontains'],
            'broadcast_type': ['exact'],
            'id': ['exact'],
            'group__name': ['icontains'],
            'owner__last_name': ['icontains']
        }


class BgOrderFilter(FilterSet):
    """Фильтрация номенклатур."""

    class Meta:
        model = BgOrder
        fields = {
            'name': ['icontains'],
            'id': ['exact'],
            'client__name': ['icontains'],
            'owner__last_name': ['icontains'],
            'order_type': ['exact']
        }
