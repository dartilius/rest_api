from django_filters import CharFilter, DateFromToRangeFilter, FilterSet

from api.constants import filter_by_owner_name
from .models import CustomUser


class CustomUserFilter(FilterSet):
    """
    Фильтрация пользователей.

    Выполняется по полям:
        name    - специальный метод
        id      - точное совпадение
        role    - точное совпадение
        created - попадание в заданный промежуток времени
    """

    name = CharFilter(method='filter_by_name', label='Фамилия Имя')
    id = CharFilter(field_name='id', lookup_expr='exact')
    role = CharFilter(field_name='role', lookup_expr='iexact')
    created = DateFromToRangeFilter(field_name='created')

    class Meta:
        model = CustomUser
        fields = ('id', 'role', 'created', 'name')

    def filter_by_name(self, queryset, name, value):
        return filter_by_owner_name(queryset, name, value)
