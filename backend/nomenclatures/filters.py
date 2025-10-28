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
            from django_filters import AllValuesMultipleFilter, CharFilter, FilterSet, UUIDFilter, BaseInFilter, OrderingFilter

            from nomenclatures.models import Nomenclature


            class UUIDCommaInFilter(BaseInFilter, UUIDFilter):
                """Поддерживает фильтрацию UUID через запятую (в URL)."""
                def filter(self, qs, value):
                    if value:
                        if isinstance(value, str):
                            value = value.split(",")
                    return super().filter(qs, value)
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
                    brand_id    - совпадение по множеству id брендов через ',' без пробела
                    code1c      - точное совпадение
                """

                versions = AllValuesMultipleFilter(field_name='version')
                version = CharFilter(field_name='version', lookup_expr='icontains')
                status = CharFilter(method='get_status', label='Статус')
                name = CharFilter(field_name='name', lookup_expr='icontains')
                id = CharFilter(field_name='id', lookup_expr='iexact')
                timezone = CharFilter(field_name='timezone', lookup_expr='iexact')
                brand_id = UUIDCommaInFilter(field_name='brand_id', lookup_expr='in')
                code1c = CharFilter(field_name="code1c", lookup_expr="icontains")

                ordering = OrderingFilter(
                    fields=(
                        ('name', 'name'),
                        ('version', 'version'),
                        ('timezone', 'timezone'),
                        ('pricePerMonth', 'pricePerMonth'),
                        ('created', 'created'),
                        ('brand__name', 'brand_name'),
                    ),
                    field_labels={
                        'name': 'Название',
                        'version': 'Версия ПО',
                        'timezone': 'Часовой пояс',
                        'code1c': 'Код 1С',
                        'pricePerMonth': 'Цена за месяц',
                        'created': 'Дата создания',
                        'brand__name': 'Название бренда',
                        'brand__code1c': 'Код 1С бренда',
                    }
                )

                class Meta:
                    model = Nomenclature
                    fields = ('name', 'id', 'timezone', 'versions', 'status', 'brand_id', "code1c")

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
