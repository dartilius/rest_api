import uuid
from django_filters import FilterSet, CharFilter, UUIDFilter, BaseInFilter, OrderingFilter
from django.db.models import Q
from .models import (
    Country, FederalDistrict, TypeRegion, Timezone, Region,
    LocalityType, City, AdministrativeTerritory,
    AdministrativeTerritorialUnit, StreetType, Street,
    House, Building, Address, Coordinates
)

# ==================== БАЗОВЫЕ КЛАССЫ ====================

class UUIDCommaInFilter(BaseInFilter, UUIDFilter):
    """Фильтр для списка UUID через запятую."""

    def filter(self, qs, value):
        if not value:
            return qs

        uuids = []
        if isinstance(value, str):
            for v in value.split(','):
                v = v.strip()
                if v:
                    try:
                        uuid.UUID(v)
                        uuids.append(v)
                    except (ValueError, AttributeError):
                        continue

        if not uuids:
            return qs

        return super().filter(qs, uuids)


class BaseFilter(FilterSet):
    """Базовый фильтр с search, ids, ordering для ВСЕХ моделей."""

    search = CharFilter(
        method='filter_search',
        label='Поиск',
        help_text='Поиск по названию'
    )

    ids = UUIDCommaInFilter(
        field_name='id',
        lookup_expr='in',
        label='Идентификаторы',
        help_text='Фильтр по ID через запятую. Пример: ?ids=uuid1,uuid2,uuid3'
    )

    ordering = OrderingFilter(
        label='Сортировка',
        help_text='Сортировка результатов. Пример: ?ordering=name'
    )

    def filter_search(self, queryset, name, value):
        """По умолчанию ищем по полю name."""
        if not value:
            return queryset
        return queryset.filter(name__icontains=value)

    class Meta:
        abstract = True


# ==================== КОНКРЕТНЫЕ ФИЛЬТРЫ ====================

class CountryFilter(BaseFilter):
    class Meta(BaseFilter.Meta):
        model = Country
        fields = ['search', 'ids']
        ordering_fields = ['name']


class FederalDistrictFilter(BaseFilter):
    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(abbreviated_name__icontains=value)
        )

    class Meta(BaseFilter.Meta):
        model = FederalDistrict
        fields = ['search', 'ids']
        ordering_fields = ['name', 'abbreviated_name']


class RegionFilter(BaseFilter):
    # ДОБАВЛЯЕМ фильтр по федеральным округам
    federal_districts = UUIDCommaInFilter(
        field_name='federal_district_id',
        lookup_expr='in',
        label='Федеральные округа',
        help_text='Фильтрация по федеральным округам. Пример: ?federal_districts=uuid-цфо,uuid-сзфо'
    )

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(abbreviated_name__icontains=value) |
            Q(federal_district__name__icontains=value)
        )

    class Meta(BaseFilter.Meta):
        model = Region
        fields = ['search', 'ids', 'federal_districts']
        ordering_fields = ['name', 'abbreviated_name', 'federal_district__name']


class CityFilter(BaseFilter):
    # ДОБАВЛЯЕМ фильтр по регионам
    regions = UUIDCommaInFilter(
        field_name='region_id',
        lookup_expr='in',
        label='Регионы',
        help_text='Фильтрация по регионам. Пример: ?regions=uuid-московская-обл,uuid-ленинградская-обл'
    )

    # ОПЦИОНАЛЬНО: фильтр по федеральным округам (через регионы)
    federal_districts = UUIDCommaInFilter(
        field_name='region__federal_district_id',
        lookup_expr='in',
        label='Федеральные округа',
        help_text='Фильтрация по федеральным округам. Пример: ?federal_districts=uuid-цфо'
    )

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(region__name__icontains=value) |
            Q(region__federal_district__name__icontains=value)
        )

    class Meta(BaseFilter.Meta):
        model = City
        fields = ['search', 'ids', 'regions', 'federal_districts']
        ordering_fields = ['name', 'region__name', 'region__federal_district__name']


class StreetFilter(BaseFilter):
    # ДОБАВЛЯЕМ фильтр по городам
    cities = UUIDCommaInFilter(
        field_name='city_id',
        lookup_expr='in',
        label='Города',
        help_text='Фильтрация по городам. Пример: ?cities=uuid-москва,uuid-спб'
    )

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(city__name__icontains=value)
        )

    class Meta(BaseFilter.Meta):
        model = Street
        fields = ['search', 'ids', 'cities']
        ordering_fields = ['name', 'city__name']


# УПРОЩЁННЫЙ AddressFilter
class AddressFilter(BaseFilter):
    """
    ФИЛЬТР ДЛЯ АДРЕСОВ ТОЛЬКО С ГЛОБАЛЬНЫМ ПОИСКОМ.

    📌 ПАРАМЕТРЫ:
    • search - универсальный поиск по всем компонентам адреса
    • ids - фильтр по ID адресов через запятую
    • ordering - сортировка

    📌 ПОИСК ИЩЕТ ПО:
    • Стране, региону, городу, улице
    • Номеру дома и строения
    • Почтовому индексу и микрорайону
    """

    def filter_search(self, queryset, name, value):
        """Глобальный поиск по всем компонентам адреса."""
        if not value:
            return queryset

        words = value.split()
        q_objects = Q()

        for word in words:
            if len(word) >= 2:
                word_q = (
                        Q(country__name__icontains=word) |  # Страна
                        Q(region__name__icontains=word) |  # Регион
                        Q(city__name__icontains=word) |  # Город
                        Q(street__name__icontains=word) |  # Улица
                        Q(house__number__icontains=word) |  # Номер дома
                        Q(building__number__icontains=word) |  # Номер строения
                        Q(microdistrict__icontains=word) |  # Микрорайон
                        Q(index__icontains=word) |  # Почтовый индекс
                        Q(administrative_territory__name__icontains=word) |  # Адм. округ
                        Q(administrative_unit__name__icontains=word)  # Район/округ
                )
                q_objects &= word_q

        return queryset.filter(q_objects).distinct()

    class Meta(BaseFilter.Meta):
        model = Address
        fields = ['search', 'ids']  # ← ТОЛЬКО search и ids!

        ordering_fields = [
            'country__name', 'region__name', 'city__name',
            'street__name', 'house__number', 'building__number',
            'index', 'microdistrict',
        ]