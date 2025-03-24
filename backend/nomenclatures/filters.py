from django_filters import AllValuesMultipleFilter, CharFilter, FilterSet

from nomenclatures.models import Nomenclature


class NomenclatureFilter(FilterSet):
    """
    Фильтрация номенклатур.

    Выполняется по полям:
        versions    - селектор из всех возможных вариантов
        version     - частичное совпадение
        status      - специальный метод
        name        - частичное совпадение
        id          - точное совпадение
        timezone    - точное совпадение
    """

    versions = AllValuesMultipleFilter(field_name='version')
    version = CharFilter(field_name='version', lookup_expr='icontains')
    status = CharFilter(method='get_status', label='Статус')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    id = CharFilter(field_name='id', lookup_expr='iexact')
    timezone = CharFilter(field_name='timezone', lookup_expr='iexact')

    class Meta:
        model = Nomenclature
        fields = ('name', 'id', 'timezone', 'versions', 'status')

    def get_status(self, queryset, name, value):
        """
        Специальный метод для фильтрации по статусам.

        Поддерживает поиск без указания статуса, для номенклатур,
        которые никогда не выходили на связь.
        При поиске по статусу, отличному от поддерживаемых (0, 1, 2),
        возвращает все номенклатуры
        """
        if value.lower() == 'null':
            return queryset.filter(availability__status=None)
        elif value in ('0', '1', '2'):
            return queryset.filter(availability__status=value)
        else:
            return queryset
