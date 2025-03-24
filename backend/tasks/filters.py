from django_filters import CharFilter, DateFromToRangeFilter, FilterSet

from api.constants import filter_by_owner_name
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

    owner = CharFilter(method='owner_filter')
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

    def owner_filter(self, queryset, name, value):
        return filter_by_owner_name(queryset, name, value)
