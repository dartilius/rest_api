from django_filters import AllValuesMultipleFilter, CharFilter, FilterSet

from nomenclatures.models import Nomenclature


class NomenclatureFilter(FilterSet):
    """Фильтрация номенклатур."""

    versions = AllValuesMultipleFilter(field_name='version')
    status = CharFilter(method='get_status')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    id = CharFilter(field_name='id', lookup_expr='iexact')
    timezone = CharFilter(field_name='timezone', lookup_expr='iexact')

    class Meta:
        model = Nomenclature
        fields = ('name', 'id', 'timezone', 'versions', 'status')

    def get_status(self, queryset, name, value):
        """Фильтрация по статусам."""
        if value.lower() == 'null':
            return queryset.filter(availability__status=None)
        elif value not in ('0', '1', '2'):
            return queryset
        else:
            return queryset.filter(availability__status=value)
