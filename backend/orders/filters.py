from uuid import UUID

from django.db.models import Q
from django_filters import CharFilter, DateFromToRangeFilter, FilterSet

from api.constants import filter_by_owner_name
from orders.models import AdOrder, BgOrder


class AdOrderFilter(FilterSet):
    """Фильтрация рекламных заказов.

    Выполняется по полям:
        owner    - специальный метод
        name     - частичное совпадение
        brc_type - точное совпадение
        id       - точное совпадение
        client   - частичное совпадение
        created  - попадание в заданный промежуток времени
    """

    owner = CharFilter(method='owner_filter')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    brc_type = CharFilter(field_name='broadcast_type', lookup_expr='exact')
    status = CharFilter(field_name='status', lookup_expr='exact')
    id = CharFilter(field_name='id', lookup_expr='exact')
    client = CharFilter(
        field_name='client__name',
        lookup_expr='icontains',
        label='Целевая рабочая станция'
    )
    nomenclature = CharFilter(method='nomenclature_filter')
    created = DateFromToRangeFilter(field_name='created')
    since = DateFromToRangeFilter(field_name='broadcast_interval__lower')
    until = DateFromToRangeFilter(field_name='broadcast_interval__upper')

    class Meta:
        model = AdOrder
        fields = (
            'name',
            'brc_type',
            'id',
            'client',
            'owner',
            'nomenclature',
            'created',
            'status',
            'since',
            'until'
        )

    def owner_filter(self, queryset, name, value):
        return filter_by_owner_name(queryset, name, value)

    def nomenclature_filter(self, queryset, name, value):
        try:
            nomenclature_id = UUID(value)
        except (TypeError, ValueError):
            id_filter = Q()
        else:
            id_filter = Q(client__id=nomenclature_id)

        return queryset.filter(
            id_filter
            | Q(client__name__icontains=value)
            | Q(client__brand__name__icontains=value)
            | Q(client__address__address__city__name__icontains=value)
            | Q(client__address__address__city__locality_type__name__icontains=value)
            | Q(client__address__address__street__name__icontains=value)
            | Q(client__address__address__street__street_type__name__icontains=value)
        ).distinct()


class BgOrderFilter(FilterSet):
    """Фильтрация фоновых заказов.

    Выполняется по полям:
        owner      - специальный метод
        name       - частичное совпадение
        id         - точное совпадение
        client     - частичное совпадение
        order_type - точное совпадение
        created    - попадание в заданный промежуток времени
    """

    owner = CharFilter(method='owner_filter')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    id = CharFilter(field_name='id', lookup_expr='exact')
    client = CharFilter(
        field_name='client__name',
        lookup_expr='icontains',
        label='Целевая рабочая станция'
    )
    order_type = CharFilter(field_name='order_type', lookup_expr='exact')
    status = CharFilter(field_name='status', lookup_expr='exact')
    nomenclature = CharFilter(method='nomenclature_filter')
    created = DateFromToRangeFilter(field_name='created')
    since = DateFromToRangeFilter(field_name='broadcast_interval__lower')
    until = DateFromToRangeFilter(field_name='broadcast_interval__upper')

    class Meta:
        model = BgOrder
        fields = (
            'name',
            'id',
            'client',
            'order_type',
            'owner',
            'nomenclature',
            'created',
            'status',
            'since',
            'until'
        )

    def owner_filter(self, queryset, name, value):
        return filter_by_owner_name(queryset, name, value)

    def nomenclature_filter(self, queryset, name, value):
        try:
            nomenclature_id = UUID(value)
        except (TypeError, ValueError):
            id_filter = Q()
        else:
            id_filter = Q(client__id=nomenclature_id)

        return queryset.filter(
            id_filter
            | Q(client__name__icontains=value)
            | Q(client__brand__name__icontains=value)
            | Q(client__address__address__city__name__icontains=value)
            | Q(client__address__address__city__locality_type__name__icontains=value)
            | Q(client__address__address__street__name__icontains=value)
            | Q(client__address__address__street__street_type__name__icontains=value)
        ).distinct()
