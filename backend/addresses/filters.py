"""
Фильтры для справочника адресов.

Фильтры позволяют искать и сортировать данные через API.
Все фильтры поддерживают:
- search — поиск по текстовым полям
- ids — фильтр по списку UUID
- ordering — сортировка
"""

import uuid
from django_filters import (
    FilterSet,
    CharFilter,
    UUIDFilter,
    BaseInFilter,
    OrderingFilter,
)
from django.db.models import Q
from .models import (
    Country,
    FederalDistrict,
    Region,
    City,
    AdministrativeTerritory,
    AdministrativeTerritorialUnit,
    Street,
    House,
    Building,
    Address,
)


class UUIDCommaInFilter(BaseInFilter, UUIDFilter):
    """Фильтр для списка UUID через запятую: ?ids=uuid1,uuid2,uuid3"""

    pass


class BaseFilter(FilterSet):
    """Базовый фильтр с общими параметрами для всех моделей."""

    search = CharFilter(method="filter_search", label="Поиск")
    ids = UUIDCommaInFilter(field_name="id", lookup_expr="in", label="ID")
    ordering = OrderingFilter(label="Сортировка")

    def filter_search(self, queryset, name, value):
        """Поиск по полю name (можно переопределить в наследниках)."""
        if not value:
            return queryset
        return queryset.filter(name__icontains=value)

    class Meta:
        abstract = True


class CountryFilter(BaseFilter):
    """Фильтр для стран. Ищет по названию."""

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(iso_code__icontains=value)
            | Q(iso3_code__icontains=value)
        )

    class Meta:
        model = Country
        fields = ["search", "ids"]
        ordering_fields = ["name"]


class RegionFilter(BaseFilter):
    """Фильтр для регионов."""

    federal_districts = UUIDCommaInFilter(
        field_name="federal_district_id", lookup_expr="in", label="Федеральные округа"
    )
    countries = UUIDCommaInFilter(
        field_name="country_id", lookup_expr="in", label="Страны"
    )

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(abbreviated_name__icontains=value)
            | Q(country__name__icontains=value)
            | Q(federal_district__name__icontains=value)
        )

    class Meta:
        model = Region
        fields = ["search", "ids", "countries", "federal_districts"]
        ordering_fields = ["name", "country__name", "federal_district__name"]


class CityFilter(BaseFilter):
    """Фильтр для городов."""

    regions = UUIDCommaInFilter(
        field_name="region_id", lookup_expr="in", label="Регионы"
    )
    federal_districts = UUIDCommaInFilter(
        field_name="region__federal_district_id",
        lookup_expr="in",
        label="Федеральные округа",
    )

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(region__name__icontains=value)
            | Q(region__federal_district__name__icontains=value)
        )

    class Meta:
        model = City
        fields = ["search", "ids", "regions", "federal_districts"]
        ordering_fields = ["name", "region__name"]


class StreetFilter(BaseFilter):
    """Фильтр для улиц."""

    cities = UUIDCommaInFilter(field_name="city_id", lookup_expr="in", label="Города")

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(city__name__icontains=value)
        )

    class Meta:
        model = Street
        fields = ["search", "ids", "cities"]
        ordering_fields = ["name", "city__name"]


class AddressFilter(BaseFilter):
    """
    Фильтр для адресов.

    Поиск работает по ВСЕМ компонентам адреса:
    стране, региону, городу, улице, дому, индексу.
    """

    country = UUIDCommaInFilter(
        field_name="country_id", lookup_expr="in", label="Страна"
    )
    region = UUIDCommaInFilter(field_name="region_id", lookup_expr="in", label="Регион")
    city = UUIDCommaInFilter(field_name="city_id", lookup_expr="in", label="Город")
    street = UUIDCommaInFilter(field_name="street_id", lookup_expr="in", label="Улица")
    index = CharFilter(field_name="index", lookup_expr="icontains", label="Индекс")

    def filter_search(self, queryset, name, value):
        """Поиск по всем компонентам адреса."""
        if not value:
            return queryset

        words = value.split()
        q_objects = Q()

        for word in words:
            if len(word) >= 2:
                word_q = (
                    Q(country__name__icontains=word)
                    | Q(region__name__icontains=word)
                    | Q(city__name__icontains=word)
                    | Q(street__name__icontains=word)
                    | Q(house__number__icontains=word)
                    | Q(building__number__icontains=word)
                    | Q(index__icontains=word)
                    | Q(microdistrict__icontains=word)
                )
                q_objects &= word_q

        return queryset.filter(q_objects).distinct()

    class Meta:
        model = Address
        fields = ["search", "ids", "country", "region", "city", "street", "index"]
        ordering_fields = [
            "country__name",
            "region__name",
            "city__name",
            "street__name",
            "house__number",
        ]
