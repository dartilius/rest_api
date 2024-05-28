from django.db.models import Q
from django_filters import CharFilter, DateFromToRangeFilter, FilterSet

from users.models import CustomUser


class CustomUserFilter(FilterSet):
    """Фильтрация пользователей."""

    name = CharFilter(method='filter_by_name', label='Фамилия Имя')
    id = CharFilter(field_name='id', lookup_expr='exact')
    role = CharFilter(field_name='role', lookup_expr='iexact')
    created = DateFromToRangeFilter(field_name='created')

    class Meta:
        model = CustomUser
        fields = ('id', 'role', 'created', 'name')

    def filter_by_name(self, queryset, name, value):
        if len(value.split()) == 2:
            first_name, last_name = value.split()
            return queryset.filter(
                (Q(last_name__icontains=last_name) &
                 Q(first_name__icontains=first_name)) |
                (Q(last_name__icontains=first_name) &
                 Q(first_name__icontains=last_name))
            )
        elif len(value.split()) == 1:
            return queryset.filter(
                Q(last_name__icontains=value) |
                Q(first_name__icontains=value)
            )
        return queryset
