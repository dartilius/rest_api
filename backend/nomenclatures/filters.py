from django_filters import AllValuesMultipleFilter
from django_filters.rest_framework import (CharFilter, FilterSet)

from nomenclatures.models import Nomenclature


class NomenclatureFilter(FilterSet):
    """Фильтрация номенклатур."""

    name = CharFilter(field_name='name', lookup_expr='icontains')
    version = CharFilter(field_name='version', lookup_expr='icontains')
    versions = AllValuesMultipleFilter(field_name='version')
    id = CharFilter(field_name='id', lookup_expr='iexact')
    status = CharFilter(method='get_status')
    timezone = CharFilter(field_name='timezone', lookup_expr='iexact')

    class Meta:
        model = Nomenclature
        fields = ('name', 'version', 'id', 'status', 'timezone')

    def get_status(self, queryset, name, value):
        """Фильтрация по статусам."""
        print(value)
        if value not in ('0', '1', '2'):
            return queryset
        else:
            return queryset.filter(status=value)
