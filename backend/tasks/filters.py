from django.db.models import Q
from django_filters import CharFilter, DateFromToRangeFilter, FilterSet

from tasks.models import Task


class TaskFilter(FilterSet):
    """Фильтрация репликаций.

    Выполняется по полям:
        owner   - специальный метод
        id      - точное совпадение
        type    - точное совпадение
        status  - точное совпадение
        client  - точное совпадение
        created - попадание в заданный промежуток времени
    """

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
