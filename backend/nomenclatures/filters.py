from django_filters import AllValuesMultipleFilter
from django_filters.rest_framework import FilterSet, CharFilter

from nomenclatures.models import Nomenclature


class NomenclatureFilter(FilterSet):
    """Фильтрация номенклатур."""
    versions = AllValuesMultipleFilter(field_name='version')
    status = CharFilter(method='get_status')

    class Meta:
        model = Nomenclature
        fields = {
            'name': ['icontains'],
            'version': ['icontains'],
            'id': ['iexact'],
            'timezone': ['iexact']
        }

    def get_status(self, queryset, name, value):
        """Фильтрация по статусам."""
        if value.lower() == 'null':
            return queryset.filter(availability__status=None)
        elif value not in ('0', '1', '2'):
            return queryset
        else:
            return queryset.filter(availability__status=value)
