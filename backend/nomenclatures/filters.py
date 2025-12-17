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
            'pricePerMonth': 'Цена за месяц',
            'created': 'Дата создания',
            'brand__name': 'Название бренда',
            'brand__code1c': 'Код 1С бренда',
        }
    )

    class Meta:
        model = Nomenclature
        fields = ('name', 'id', 'timezone', 'versions', 'status', 'brand_id')

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


# filters.py
import django_filters
from django.db import models
from .models import Nomenclature


class UniversalNomenclatureFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='universal_search')

    class Meta:
        model = Nomenclature
        fields = ['search']

    def universal_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                models.Q(typeOfPlace__icontains=value) |
                models.Q(brand__name__icontains=value) |
                models.Q(legalEntity__name__icontains=value) |
                models.Q(tenants__name__icontains=value) |
                models.Q(responsible_radio__username__icontains=value) |
                models.Q(responsible_radio__first_name__icontains=value) |
                models.Q(responsible_radio__last_name__icontains=value) |
                models.Q(responsible_radio__email__icontains=value) |
                models.Q(responsible_ad__username__icontains=value) |
                models.Q(responsible_ad__first_name__icontains=value) |
                models.Q(responsible_ad__last_name__icontains=value) |
                models.Q(responsible_ad__email__icontains=value)
            ).distinct()
        return queryset