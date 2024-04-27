from django_filters.rest_framework import (CharFilter, FilterSet)

from nomenclatures.models import Nomenclature


class NomenclatureFilter(FilterSet):
    """Фильтрация номенклатур."""

    name = CharFilter(field_name='name', lookup_expr='istartswith')
    version = CharFilter(field_name='version', lookup_expr='icontains')
    id = CharFilter(field_name='id', lookup_expr='iexact')
    status = CharFilter(field_name='status', lookup_expr='iexact')
    timezone = CharFilter(field_name='timezone', lookup_expr='iexact')

    class Meta:
        model = Nomenclature
        fields = ('name', 'version', 'id', 'status', 'timezone')
