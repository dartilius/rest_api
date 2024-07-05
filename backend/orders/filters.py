from django.db.models import Q
from django_filters import CharFilter, DateFromToRangeFilter, FilterSet

from orders.models import AdOrder, BgOrder


class AdOrderFilter(FilterSet):
    """Фильтрация рекламных заказов.

    Выполняется по полям:
        owner    - специальный метод
        name     - частичное совпадение
        brc_type - точное совпадение
        id       - точное совпадение
        group    - частичное совпадение
        created  - попадание в заданный промежуток времени
    """

    owner = CharFilter(method='filter_by_owner_name')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    brc_type = CharFilter(field_name='broadcast_type', lookup_expr='exact')
    id = CharFilter(field_name='id', lookup_expr='exact')
    group = CharFilter(
        field_name='group__name',
        lookup_expr='icontains',
        label='Целевая группа Целевая рабочих станций'
    )
    created = DateFromToRangeFilter(field_name='created')

    class Meta:
        model = AdOrder
        fields = ('name', 'brc_type', 'id', 'group', 'owner', 'created')

    def filter_by_owner_name(self, queryset, name, value):
        """
        Специальный метод для фильтрации по имени и фамилии создателя.

        Поддерживает поиск по фамилии и имени, указанным
        вместе в любом порядке либо отдельно по фамилии или имени.
        При не совпадении или указании более двух аргументов
        возвращает список всех пользователей.
        """
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
    """Фильтрация фоновых заказов.

    Выполняется по полям:
        owner      - специальный метод
        name       - частичное совпадение
        id         - точное совпадение
        client     - частичное совпадение
        order_type - точное совпадение
        created    - попадание в заданный промежуток времени
    """

    owner = CharFilter(method='filter_by_owner_name')
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

    def filter_by_owner_name(self, queryset, name, value):
        """
        Специальный метод для фильтрации по имени и фамилии создателя.

        Поддерживает поиск по фамилии и имени, указанным
        вместе в любом порядке либо отдельно по фамилии или имени.
        При не совпадении или указании более двух аргументов
        ничего не возвращает.
        """
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
