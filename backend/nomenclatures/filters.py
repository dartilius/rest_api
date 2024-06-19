from django_filters import AllValuesMultipleFilter, CharFilter, FilterSet

from nomenclatures.models import Nomenclature


class NomenclatureFilter(FilterSet):
    """
    Фильтрация номенклатур.

    Выполняется по полям:
        versions    - точное совпадение из множества вариантов
        status      - специальный метод
        name        - частичное совпадение
        id          - точное совпадение
        timezone    - точное совпадение
    """

    versions = AllValuesMultipleFilter(field_name='version')
    status = CharFilter(method='get_status')
    name = CharFilter(field_name='name')
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
