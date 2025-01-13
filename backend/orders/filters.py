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
    id = CharFilter(field_name='id', lookup_expr='exact')
    client = CharFilter(
        field_name='client__name',
        lookup_expr='icontains',
        label='Целевая рабочая станция'
    )
    created = DateFromToRangeFilter(field_name='created')

    class Meta:
        model = AdOrder
        fields = ('name', 'brc_type', 'id', 'client', 'owner', 'created')

    def owner_filter(self, queryset, name, value):
        return filter_by_owner_name(queryset, name, value)


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
    created = DateFromToRangeFilter(field_name='created')

    class Meta:
        model = BgOrder
        fields = ('name', 'id', 'client', 'order_type', 'owner', 'created')

    def owner_filter(self, queryset, name, value):
        return filter_by_owner_name(queryset, name, value)
