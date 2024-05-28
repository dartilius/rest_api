from django.db.models import Q
from django_filters import CharFilter, FilterSet

from orders.models import AdOrder, BgOrder


class AdOrderFilter(FilterSet):
    """Фильтрация рекламных заказов."""

    owner = CharFilter(method='filter_by_owner_name')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    brc_type = CharFilter(field_name='broadcast_type', lookup_expr='exact')
    id = CharFilter(field_name='id', lookup_expr='exact')
    group = CharFilter(
        field_name='group__name',
        lookup_expr='icontains',
        label='Целевая группа Целевая рабочих станций'
    )

    class Meta:
        model = AdOrder
        fields = ('name', 'brc_type', 'id', 'group', 'owner')

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


class BgOrderFilter(FilterSet):
    """Фильтрация фоновых заказов."""

    owner = CharFilter(method='filter_by_owner_name')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    id = CharFilter(field_name='id', lookup_expr='exact')
    client = CharFilter(
        field_name='client__name',
        lookup_expr='icontains',
        label='Целевая рабочая станция'
    )
    order_type = CharFilter(field_name='order_type', lookup_expr='exact')

    class Meta:
        model = BgOrder
        fields = ('name', 'id', 'client', 'order_type', 'owner')

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
