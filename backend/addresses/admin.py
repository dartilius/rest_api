"""
Административный интерфейс (Django Admin) для справочника адресов.
Версия с полной оптимизацией запросов к базе данных.
"""

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from dal import autocomplete

from .models import (
    Country, FederalDistrict, TypeRegion, Timezone, Region,
    LocalityType, City, AdministrativeTerritory,
    AdministrativeTerritorialUnit, StreetType, Street,
    House, Building, Address, Coordinates
)


# ====================================================================================
# МОДУЛЬ 1: ОПТИМИЗИРОВАННЫЕ ФИЛЬТРЫ
# ====================================================================================

class OptimizedCountryFilter(SimpleListFilter):
    """Оптимизированный фильтр по стране"""
    title = 'Страна'
    parameter_name = 'country'
    
    def lookups(self, request, model_admin):
        # Один запрос с only()
        countries = Country.objects.only('id', 'name').order_by('name')
        return [(str(c.id), c.name) for c in countries]
    
    def queryset(self, request, queryset):
        if self.value():
            if hasattr(queryset.model, 'country'):
                return queryset.filter(country_id=self.value())
            elif hasattr(queryset.model, 'federal_district'):
                return queryset.filter(federal_district__country_id=self.value())
            elif hasattr(queryset.model, 'region'):
                return queryset.filter(region__federal_district__country_id=self.value())
            elif hasattr(queryset.model, 'city'):
                return queryset.filter(city__region__federal_district__country_id=self.value())
            elif hasattr(queryset.model, 'street'):
                return queryset.filter(street__city__region__federal_district__country_id=self.value())
        return queryset


class OptimizedRegionFilter(SimpleListFilter):
    """Оптимизированный фильтр по региону"""
    title = 'Регион'
    parameter_name = 'region'
    
    def lookups(self, request, model_admin):
        # Один запрос с select_related
        regions = Region.objects.select_related('type_region').only(
            'id', 'name', 'type_region__id', 'type_region__name',
            'type_region__abbreviated_name', 'type_region__show_before_name',
            'type_region__skip_in_name'
        ).order_by('name')
        
        choices = []
        for r in regions:
            if r.type_region and not r.type_region.skip_in_name:
                if r.type_region.show_before_name:
                    display = f"{r.type_region.abbreviated_name} {r.name}"
                else:
                    display = f"{r.name} {r.type_region.abbreviated_name}"
            else:
                display = r.name
            choices.append((str(r.id), display))
        return choices
    
    def queryset(self, request, queryset):
        if self.value():
            if hasattr(queryset.model, 'region'):
                return queryset.filter(region_id=self.value())
            elif hasattr(queryset.model, 'city'):
                return queryset.filter(city__region_id=self.value())
            elif hasattr(queryset.model, 'street'):
                return queryset.filter(street__city__region_id=self.value())
        return queryset


class OptimizedCityFilter(SimpleListFilter):
    """Оптимизированный фильтр по городу"""
    title = 'Город'
    parameter_name = 'city'
    
    def lookups(self, request, model_admin):
        # Один запрос с select_related
        cities = City.objects.select_related('locality_type').only(
            'id', 'name', 'locality_type__id', 'locality_type__name',
            'locality_type__abbreviated_name', 'locality_type__show_before_name'
        ).order_by('name')
        
        choices = []
        for c in cities:
            if c.locality_type:
                if c.locality_type.show_before_name:
                    prefix = c.locality_type.abbreviated_name or c.locality_type.name
                    display = f"{prefix} {c.name}"
                else:
                    suffix = c.locality_type.abbreviated_name or c.locality_type.name
                    display = f"{c.name} {suffix}"
            else:
                display = c.name
            choices.append((str(c.id), display))
        return choices
    
    def queryset(self, request, queryset):
        if self.value():
            if hasattr(queryset.model, 'city'):
                return queryset.filter(city_id=self.value())
            elif hasattr(queryset.model, 'street'):
                return queryset.filter(street__city_id=self.value())
        return queryset


# ====================================================================================
# МОДУЛЬ 2: ВСЕ КЛАССЫ АВТОКОМПЛИТА (для urls.py)
# ====================================================================================

class FederalDistrictAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = FederalDistrict.objects.select_related('country').only(
            'id', 'name', 'abbreviated_name', 'country__name'
        )
        country_id = self.forwarded.get('country', None)
        if country_id:
            qs = qs.filter(country_id=country_id)
        if self.q:
            qs = qs.filter(Q(name__icontains=self.q) | Q(abbreviated_name__icontains=self.q))
        return qs.order_by('country__name', 'name')[:50]
    
    def get_result_label(self, result):
        return f"{result.name} ({result.country.name})"


class RegionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Region.objects.select_related('type_region', 'federal_district').only(
            'id', 'name', 'type_region__id', 'type_region__name',
            'type_region__abbreviated_name', 'type_region__show_before_name',
            'type_region__skip_in_name', 'federal_district__name'
        )
        fd_id = self.forwarded.get('federal_district', None)
        if fd_id:
            qs = qs.filter(federal_district_id=fd_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.order_by('name')[:50]
    
    def get_result_label(self, result):
        if result.type_region and not result.type_region.skip_in_name:
            if result.type_region.show_before_name:
                return f"{result.type_region.abbreviated_name} {result.name}"
            else:
                return f"{result.name} {result.type_region.abbreviated_name}"
        return result.name


class CityAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = City.objects.select_related('region', 'locality_type').only(
            'id', 'name', 'region__name', 'locality_type__id',
            'locality_type__name', 'locality_type__abbreviated_name',
            'locality_type__show_before_name'
        )
        region_id = self.forwarded.get('region', None)
        if region_id:
            qs = qs.filter(region_id=region_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.order_by('region__name', 'name')[:50]
    
    def get_result_label(self, result):
        if result.locality_type:
            if result.locality_type.show_before_name:
                prefix = result.locality_type.abbreviated_name or result.locality_type.name
                return f"{prefix} {result.name}"
            else:
                suffix = result.locality_type.abbreviated_name or result.locality_type.name
                return f"{result.name} {suffix}"
        return result.name


class AdministrativeTerritoryAutocomplete(autocomplete.Select2QuerySetView):
    """Автокомплит для административных округов"""
    def get_queryset(self):
        qs = AdministrativeTerritory.objects.select_related('city').only(
            'id', 'name', 'city__name'
        )
        city_id = self.forwarded.get('city', None)
        if city_id:
            qs = qs.filter(city_id=city_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.order_by('city__name', 'name')[:50]
    
    def get_result_label(self, result):
        return f"{result.name} ({result.city.name})"


class AdministrativeUnitAutocomplete(autocomplete.Select2QuerySetView):
    """Автокомплит для административно-территориальных единиц"""
    def get_queryset(self):
        qs = AdministrativeTerritorialUnit.objects.select_related(
            'city', 'administrative_territory'
        ).only('id', 'name', 'city__name', 'administrative_territory__name')
        
        city_id = self.forwarded.get('city', None)
        if city_id:
            qs = qs.filter(city_id=city_id)
        
        admin_territory_id = self.forwarded.get('administrative_territory', None)
        if admin_territory_id:
            qs = qs.filter(administrative_territory_id=admin_territory_id)
        
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        
        return qs.order_by('city__name', 'name')[:50]
    
    def get_result_label(self, result):
        if result.administrative_territory:
            return f"{result.name} ({result.administrative_territory.name})"
        return f"{result.name} ({result.city.name})"


class StreetAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Street.objects.select_related('city', 'street_type').only(
            'id', 'name', 'city__name', 'street_type__id',
            'street_type__name', 'street_type__abbreviated_name',
            'street_type__show_before_name'
        )
        city_id = self.forwarded.get('city', None)
        if city_id:
            qs = qs.filter(city_id=city_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.order_by('city__name', 'name')[:50]
    
    def get_result_label(self, result):
        if result.street_type:
            if result.street_type.show_before_name:
                prefix = result.street_type.abbreviated_name or result.street_type.name
                return f"{prefix} {result.name}"
            else:
                suffix = result.street_type.abbreviated_name or result.street_type.name
                return f"{result.name} {suffix}"
        return result.name


class HouseAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = House.objects.select_related('street', 'street__city').only(
            'id', 'number', 'street__name', 'street__city__name'
        )
        street_id = self.forwarded.get('street', None)
        if street_id:
            qs = qs.filter(street_id=street_id)
        if self.q:
            qs = qs.filter(number__icontains=self.q)
        return qs.order_by('street__name', 'number')[:50]
    
    def get_result_label(self, result):
        return f"{result.street}, д. {result.number}"


class BuildingAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Building.objects.select_related('house', 'house__street', 'house__street__city').only(
            'id', 'number', 'house__number', 'house__street__name', 'house__street__city__name'
        )
        house_id = self.forwarded.get('house', None)
        if house_id:
            qs = qs.filter(house_id=house_id)
        if self.q:
            qs = qs.filter(number__icontains=self.q)
        return qs.order_by('house__street__name', 'house__number', 'number')[:50]
    
    def get_result_label(self, result):
        return f"{result.house.street}, д. {result.house.number}, стр. {result.number}"


class CoordinatesAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Coordinates.objects.only('id', 'latitude', 'longitude')
        if self.q:
            qs = qs.filter(Q(latitude__icontains=self.q) | Q(longitude__icontains=self.q))
        return qs.order_by('latitude', 'longitude')[:50]
    
    def get_result_label(self, result):
        return f"Широта: {result.latitude}, Долгота: {result.longitude}"


# ====================================================================================
# МОДУЛЬ 3: MODELADMIN КЛАССЫ
# ====================================================================================

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).only('id', 'name')


@admin.register(FederalDistrict)
class FederalDistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviated_name', 'country')
    search_fields = ('name', 'abbreviated_name')
    list_filter = (OptimizedCountryFilter,)
    autocomplete_fields = ('country',)
    ordering = ('country__name', 'name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('country').only(
            'id', 'name', 'abbreviated_name', 'country__id', 'country__name'
        )


@admin.register(TypeRegion)
class TypeRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviated_name', 'show_before_name', 'skip_in_name')
    search_fields = ('name', 'abbreviated_name')
    list_filter = ('show_before_name', 'skip_in_name')
    ordering = ('name',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).only(
            'id', 'name', 'abbreviated_name', 'show_before_name', 'skip_in_name'
        )


@admin.register(Timezone)
class TimezoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'offset_utc_display', 'offset_moscow_display')
    search_fields = ('name',)
    ordering = ('offset_utc', 'name')
    
    def offset_utc_display(self, obj):
        return f"UTC{obj.offset_utc:+d}"
    offset_utc_display.short_description = 'Смещение UTC'
    
    def offset_moscow_display(self, obj):
        return f"МСК{obj.offset_moscow:+d}"
    offset_moscow_display.short_description = 'Смещение МСК'
    
    def get_queryset(self, request):
        return super().get_queryset(request).only('id', 'name', 'offset_utc', 'offset_moscow')


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('get_display_name', 'type_region', 'federal_district', 'timezone')
    search_fields = ('name', 'abbreviated_name')
    list_filter = (OptimizedCountryFilter, OptimizedRegionFilter, 'timezone')
    autocomplete_fields = ('federal_district', 'type_region', 'timezone')
    ordering = ('federal_district__name', 'name')
    
    def get_display_name(self, obj):
        return str(obj)
    get_display_name.short_description = 'Регион'
    get_display_name.admin_order_field = 'name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'federal_district', 'type_region', 'timezone'
        ).only(
            'id', 'name', 'abbreviated_name',
            'federal_district__id', 'federal_district__name',
            'type_region__id', 'type_region__name', 'type_region__abbreviated_name',
            'type_region__show_before_name', 'type_region__skip_in_name',
            'timezone__id', 'timezone__name'
        )


@admin.register(LocalityType)
class LocalityTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviated_name', 'show_before_name', 'has_administrative_territory')
    search_fields = ('name', 'abbreviated_name')
    list_filter = ('show_before_name', 'has_administrative_territory')
    ordering = ('name',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).only(
            'id', 'name', 'abbreviated_name', 'show_before_name', 'has_administrative_territory'
        )


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('get_display_name', 'locality_type', 'region', 'timezone')
    search_fields = ('name',)
    list_filter = (OptimizedCountryFilter, OptimizedRegionFilter, OptimizedCityFilter, 'timezone')
    autocomplete_fields = ('region', 'locality_type', 'timezone')
    ordering = ('region__name', 'name')
    
    def get_display_name(self, obj):
        return str(obj)
    get_display_name.short_description = 'Город'
    get_display_name.admin_order_field = 'name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'region', 'locality_type', 'timezone'
        ).only(
            'id', 'name',
            'region__id', 'region__name',
            'locality_type__id', 'locality_type__name', 'locality_type__abbreviated_name',
            'locality_type__show_before_name',
            'timezone__id', 'timezone__name'
        )


@admin.register(AdministrativeTerritory)
class AdministrativeTerritoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'city')
    search_fields = ('name',)
    list_filter = (OptimizedCityFilter,)
    autocomplete_fields = ('city',)
    ordering = ('city__name', 'name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('city').only(
            'id', 'name', 'city__id', 'city__name'
        )


@admin.register(AdministrativeTerritorialUnit)
class AdministrativeUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'administrative_territory')
    search_fields = ('name',)
    list_filter = (OptimizedCityFilter, 'administrative_territory')
    autocomplete_fields = ('city', 'administrative_territory')
    ordering = ('city__name', 'name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'city', 'administrative_territory'
        ).only(
            'id', 'name', 'city__id', 'city__name',
            'administrative_territory__id', 'administrative_territory__name'
        )


@admin.register(StreetType)
class StreetTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviated_name', 'show_before_name')
    search_fields = ('name', 'abbreviated_name')
    list_filter = ('show_before_name',)
    ordering = ('name',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).only(
            'id', 'name', 'abbreviated_name', 'show_before_name'
        )


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    list_display = ('get_display_name', 'street_type', 'city')
    search_fields = ('name',)
    list_filter = (OptimizedCountryFilter, OptimizedRegionFilter, OptimizedCityFilter)
    autocomplete_fields = ('city', 'street_type')
    ordering = ('city__name', 'name')
    
    def get_display_name(self, obj):
        return str(obj)
    get_display_name.short_description = 'Улица'
    get_display_name.admin_order_field = 'name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('city', 'street_type').only(
            'id', 'name',
            'city__id', 'city__name',
            'street_type__id', 'street_type__name', 'street_type__abbreviated_name',
            'street_type__show_before_name'
        )


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('number', 'street', 'get_city')
    search_fields = ('number',)
    list_filter = ('street',)
    autocomplete_fields = ('street',)
    ordering = ('street__name', 'number')
    
    def get_city(self, obj):
        return obj.street.city.name if obj.street and obj.street.city else '-'
    get_city.short_description = 'Город'
    get_city.admin_order_field = 'street__city__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'street', 'street__city'
        ).only(
            'id', 'number',
            'street__id', 'street__name',
            'street__city__id', 'street__city__name'
        )


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('number', 'house', 'get_street', 'get_city')
    search_fields = ('number',)
    list_filter = ('house',)
    autocomplete_fields = ('house',)
    ordering = ('house__street__name', 'house__number', 'number')
    
    def get_street(self, obj):
        return obj.house.street.name if obj.house and obj.house.street else '-'
    get_street.short_description = 'Улица'
    get_street.admin_order_field = 'house__street__name'
    
    def get_city(self, obj):
        if obj.house and obj.house.street and obj.house.street.city:
            return obj.house.street.city.name
        return '-'
    get_city.short_description = 'Город'
    get_city.admin_order_field = 'house__street__city__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'house', 'house__street', 'house__street__city'
        ).only(
            'id', 'number',
            'house__id', 'house__number',
            'house__street__id', 'house__street__name',
            'house__street__city__id', 'house__street__city__name'
        )


@admin.register(Coordinates)
class CoordinatesAdmin(admin.ModelAdmin):
    list_display = ('latitude', 'longitude')
    search_fields = ('latitude', 'longitude')
    ordering = ('latitude', 'longitude')
    
    def get_queryset(self, request):
        return super().get_queryset(request).only('id', 'latitude', 'longitude')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Административный класс для управления адресами (оптимизированный)"""
    
    list_display = (
        'full_address_display',
        'get_country_name',
        'get_region_name',
        'get_city_name',
        'get_street_name',
        'get_house_number',
        'get_building_number',
        'index'
    )
    
    search_fields = (
        'country__name', 'region__name', 'city__name', 'street__name',
        'house__number', 'building__number', 'microdistrict', 'index'
    )
    
    list_filter = (OptimizedCountryFilter, OptimizedRegionFilter, OptimizedCityFilter)
    
    autocomplete_fields = (
        'country', 'federal_district', 'region', 'city',
        'administrative_territory', 'administrative_unit',
        'street', 'house', 'building', 'coordinates'
    )
    
    readonly_fields = ('full_address',)
    
    ordering = ('country__name', 'region__name', 'city__name', 'street__name', 'house__number', 'building__number')
    
    fieldsets = (
        ('Основная информация', {'fields': ('country', 'federal_district', 'region', 'city', 'full_address')}),
        ('Административное деление', {'fields': ('administrative_territory', 'administrative_unit'), 'classes': ('collapse',)}),
        ('Улично-домовая сеть', {'fields': ('street', 'house', 'building')}),
        ('Координаты', {'fields': ('coordinates',)}),
        ('Дополнительная информация', {'fields': ('microdistrict', 'index'), 'classes': ('collapse',)}),
    )
    
    def full_address_display(self, obj):
        return obj.full_address[:100]
    full_address_display.short_description = 'Полный адрес'
    
    def get_country_name(self, obj):
        return obj.country.name if obj.country else '-'
    get_country_name.short_description = 'Страна'
    get_country_name.admin_order_field = 'country__name'
    
    def get_region_name(self, obj):
        return str(obj.region) if obj.region else '-'
    get_region_name.short_description = 'Регион'
    get_region_name.admin_order_field = 'region__name'
    
    def get_city_name(self, obj):
        return str(obj.city) if obj.city else '-'
    get_city_name.short_description = 'Город'
    get_city_name.admin_order_field = 'city__name'
    
    def get_street_name(self, obj):
        return str(obj.street) if obj.street else '-'
    get_street_name.short_description = 'Улица'
    get_street_name.admin_order_field = 'street__name'
    
    def get_house_number(self, obj):
        return obj.house.number if obj.house else '-'
    get_house_number.short_description = 'Дом'
    get_house_number.admin_order_field = 'house__number'
    
    def get_building_number(self, obj):
        return obj.building.number if obj.building else '-'
    get_building_number.short_description = 'Строение'
    get_building_number.admin_order_field = 'building__number'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'country', 'federal_district',
            'region__type_region', 'city__locality_type',
            'administrative_territory', 'administrative_unit',
            'street__street_type', 'house', 'building', 'coordinates'
        ).only(
            'id', 'microdistrict', 'index',
            'country__id', 'country__name',
            'federal_district__id', 'federal_district__name',
            'region__id', 'region__name',
            'region__type_region__id', 'region__type_region__name',
            'region__type_region__abbreviated_name',
            'region__type_region__show_before_name', 'region__type_region__skip_in_name',
            'city__id', 'city__name',
            'city__locality_type__id', 'city__locality_type__name',
            'city__locality_type__abbreviated_name', 'city__locality_type__show_before_name',
            'administrative_territory__id', 'administrative_territory__name',
            'administrative_unit__id', 'administrative_unit__name',
            'street__id', 'street__name',
            'street__street_type__id', 'street__street_type__name',
            'street__street_type__abbreviated_name', 'street__street_type__show_before_name',
            'house__id', 'house__number',
            'building__id', 'building__number',
            'coordinates__id', 'coordinates__latitude', 'coordinates__longitude',
        )
    
    def save_model(self, request, obj, form, change):
        if obj.region and not obj.country:
            obj.country = obj.region.federal_district.country
        if obj.region and not obj.federal_district:
            obj.federal_district = obj.region.federal_district
        if obj.city and not obj.region:
            obj.region = obj.city.region
        if obj.street and not obj.city:
            obj.city = obj.street.city
        if obj.house and not obj.street:
            obj.street = obj.house.street
        if obj.building and not obj.house:
            obj.house = obj.building.house
        super().save_model(request, obj, form, change)
    
    def full_address(self, obj):
        return format_html('<strong>{}</strong>', obj.full_address)
    full_address.short_description = 'Полный адрес (автоматически)'


# """
# Административный интерфейс (Django Admin) для справочника адресов.

# МОДУЛЬ ADMIN:
# ─────────────────────────────────────────────────────────────────────────────────────
# Этот модуль настраивает отображение моделей адресов в административном интерфейсе Django.
# Использует django-autocomplete-light (DAL) для улучшения пользовательского опыта.

# ДОБАВЛЕННАЯ ФУНКЦИОНАЛЬНОСТЬ:
# • Поддержка модели Coordinates (координаты) с автокомплитом
# • Интеграция координат в адресную иерархию
# • Поиск и фильтрация по координатам в админке

# СТРУКТУРА МОДУЛЯ:
# ─────────────────────────────────────────────────────────────────────────────────────
# 1. Autocomplete Views
#    • Для всех моделей с зависимостями
#    • Поддержка цепочек зависимостей (например, улица зависит от города)
#    • Поиск по текстовым полям
#    • Добавлен CoordinatesAutocomplete для работы с координатами

# 2. ModelAdmin классы
#    • Для каждой модели адреса
#    • Настройка отображения, поиска, фильтрации
#    • Использование autocomplete_fields для связанных полей
#    • Добавлен CoordinatesAdmin для управления координатами

# 3. Фильтры для админки
#    • CountryFilter - фильтрация по стране
#    • RegionFilter - фильтрация по региону
#    • CityFilter - фильтрация по городу

# ОСОБЕННОСТИ:
# • Иерархическое отображение адресов с поддержкой координат
# • Быстрый поиск по всем полям, включая координаты
# • Автозаполнение зависимых полей через autocomplete
# • Валидация целостности данных адресной иерархии
# • Поддержка географических координат в составе адреса

# ИСПОЛЬЗУЕМЫЕ БИБЛИОТЕКИ:
# • django.contrib.admin
# • dal (django-autocomplete-light)
# """

# from django.contrib import admin
# from django.contrib.admin import SimpleListFilter
# from django.utils.html import format_html
# from dal import autocomplete

# from .models import (
#     Country, FederalDistrict, TypeRegion, Timezone, Region,
#     LocalityType, City, AdministrativeTerritory,
#     AdministrativeTerritorialUnit, StreetType, Street,
#     House, Building, Address, Coordinates
# )


# # ====================================================================================
# # МОДУЛЬ 1: КЛАССЫ ДЛЯ АВТОКОМПЛИТА (AUTOCOMPLETE)
# # ====================================================================================

# class FederalDistrictAutocomplete(autocomplete.Select2QuerySetView):
#     """
#     АВТОКОМПЛИТ ДЛЯ ФЕДЕРАЛЬНЫХ ОКРУГОВ.

#     ОСОБЕННОСТИ:
#         • Фильтрация по стране (если передана в forwarded)
#         • Поиск по названию федерального округа
#         • Сортировка по названию

#     ИСПОЛЬЗУЕТСЯ В:
#         • Административном интерфейсе для поля FederalDistrict
#         • Формах создания/редактирования регионов
#     """

#     def get_queryset(self):
#         """
#         ПОЛУЧЕНИЕ QUERYSET ДЛЯ АВТОКОМПЛИТА.

#         ЛОГИКА:
#             1. Начинаем с всех федеральных округов
#             2. Фильтруем по стране, если она передана
#             3. Фильтруем по поисковому запросу
#             4. Сортируем по названию

#         ВОЗВРАЩАЕТ:
#             QuerySet: Отфильтрованный queryset федеральных округов
#         """
#         qs = FederalDistrict.objects.all().select_related('country')

#         # Фильтрация по стране (если передана)
#         country_id = self.forwarded.get('country', None)
#         if country_id:
#             qs = qs.filter(country_id=country_id)

#         # Поиск по названию
#         if self.q:
#             qs = qs.filter(name__icontains=self.q)

#         return qs.order_by('country__name', 'name')


# class RegionAutocomplete(autocomplete.Select2QuerySetView):
#     """
#     АВТОКОМПЛИТ ДЛЯ РЕГИОНОВ.

#     ОСОБЕННОСТИ:
#         • Фильтрация по федеральному округу
#         • Поиск по названию региона
#         • Учет типа региона в отображении
#     """

#     def get_queryset(self):
#         """Получение queryset для регионов с фильтрацией."""
#         qs = Region.objects.all().select_related(
#             'federal_district', 'type_region', 'timezone'
#         )

#         # Фильтрация по федеральному округу
#         fd_id = self.forwarded.get('federal_district', None)
#         if fd_id:
#             qs = qs.filter(federal_district_id=fd_id)

#         # Поиск по названию
#         if self.q:
#             qs = qs.filter(name__icontains=self.q)

#         return qs.order_by('federal_district__name', 'name')

#     def get_result_label(self, result):
#         """
#         ФОРМАТИРОВАНИЕ НАЗВАНИЯ РЕГИОНА ДЛЯ ОТОБРАЖЕНИЯ.

#         АРГУМЕНТЫ:
#             result : Region
#                 Объект региона

#         ВОЗВРАЩАЕТ:
#             str: Отформатированное название региона
#         """
#         return str(result)


# class CityAutocomplete(autocomplete.Select2QuerySetView):
#     """
#     АВТОКОМПЛИТ ДЛЯ ГОРОДОВ.

#     ОСОБЕННОСТИ:
#         • Фильтрация по региону
#         • Поиск по названию города
#         • Учет типа населенного пункта в отображении
#     """

#     def get_queryset(self):
#         """Получение queryset для городов с фильтрацией."""
#         qs = City.objects.all().select_related('region', 'locality_type', 'timezone')

#         # Фильтрация по региону
#         region_id = self.forwarded.get('region', None)
#         if region_id:
#             qs = qs.filter(region_id=region_id)

#         # Поиск по названию
#         if self.q:
#             qs = qs.filter(name__icontains=self.q)

#         return qs.order_by('region__name', 'name')

#     def get_result_label(self, result):
#         """Форматирование названия города для отображения."""
#         return str(result)


# class AdministrativeTerritoryAutocomplete(autocomplete.Select2QuerySetView):
#     """
#     АВТОКОМПЛИТ ДЛЯ АДМИНИСТРАТИВНЫХ ОКРУГОВ.

#     ОСОБЕННОСТИ:
#         • Фильтрация по городу
#         • Поиск по названию округа
#         • Только для городов с has_administrative_territory=True
#     """

#     def get_queryset(self):
#         """Получение queryset для административных округов."""
#         qs = AdministrativeTerritory.objects.all().select_related('city')

#         # Фильтрация по городу
#         city_id = self.forwarded.get('city', None)
#         if city_id:
#             qs = qs.filter(city_id=city_id)

#         # Поиск по названию
#         if self.q:
#             qs = qs.filter(name__icontains=self.q)

#         return qs.order_by('city__name', 'name')


# class AdministrativeUnitAutocomplete(autocomplete.Select2QuerySetView):
#     """
#     АВТОКОМПЛИТ ДЛЯ АДМИНИСТРАТИВНО-ТЕРРИТОРИАЛЬНЫХ ЕДИНИЦ.

#     ОСОБЕННОСТИ:
#         • Фильтрация по городу
#         • Фильтрация по административному округу (опционально)
#         • Поиск по названию АТЕ
#     """

#     def get_queryset(self):
#         """Получение queryset для административно-территориальных единиц."""
#         qs = AdministrativeTerritorialUnit.objects.all().select_related(
#             'city', 'administrative_territory'
#         )

#         # Фильтрация по городу
#         city_id = self.forwarded.get('city', None)
#         if city_id:
#             qs = qs.filter(city_id=city_id)

#         # Фильтрация по административному округу
#         admin_territory_id = self.forwarded.get('administrative_territory', None)
#         if admin_territory_id:
#             qs = qs.filter(administrative_territory_id=admin_territory_id)

#         # Поиск по названию
#         if self.q:
#             qs = qs.filter(name__icontains=self.q)

#         return qs.order_by('city__name', 'name')


# class StreetAutocomplete(autocomplete.Select2QuerySetView):
#     """
#     АВТОКОМПЛИТ ДЛЯ УЛИЦ.

#     ОСОБЕННОСТИ:
#         • Фильтрация по городу
#         • Поиск по названию улицы
#         • Учет типа улицы в отображении
#     """

#     def get_queryset(self):
#         """Получение queryset для улиц."""
#         qs = Street.objects.all().select_related('city', 'street_type')

#         # Фильтрация по городу
#         city_id = self.forwarded.get('city', None)
#         if city_id:
#             qs = qs.filter(city_id=city_id)

#         # Поиск по названию
#         if self.q:
#             qs = qs.filter(name__icontains=self.q)

#         return qs.order_by('city__name', 'name')

#     def get_result_label(self, result):
#         """Форматирование названия улицы для отображения."""
#         return str(result)


# class HouseAutocomplete(autocomplete.Select2QuerySetView):
#     """
#     АВТОКОМПЛИТ ДЛЯ ДОМОВ.

#     ОСОБЕННОСТИ:
#         • Фильтрация по улице
#         • Поиск по номеру дома
#         • Отображение с названием улицы
#     """

#     def get_queryset(self):
#         """Получение queryset для домов."""
#         qs = House.objects.all().select_related('street')

#         # Фильтрация по улице
#         street_id = self.forwarded.get('street', None)
#         if street_id:
#             qs = qs.filter(street_id=street_id)

#         # Поиск по номеру дома
#         if self.q:
#             qs = qs.filter(number__icontains=self.q)

#         return qs.order_by('street__name', 'number')

#     def get_result_label(self, result):
#         """Форматирование дома для отображения."""
#         return f"{result.street}, д. {result.number}"


# class BuildingAutocomplete(autocomplete.Select2QuerySetView):
#     """
#     АВТОКОМПЛИТ ДЛЯ СТРОЕНИЙ.

#     ОСОБЕННОСТИ:
#         • Фильтрация по дому
#         • Поиск по номеру строения
#         • Отображение с полным адресом дома
#     """

#     def get_queryset(self):
#         """Получение queryset для строений."""
#         qs = Building.objects.all().select_related('house', 'house__street')

#         # Фильтрация по дому
#         house_id = self.forwarded.get('house', None)
#         if house_id:
#             qs = qs.filter(house_id=house_id)

#         # Поиск по номеру строения
#         if self.q:
#             qs = qs.filter(number__icontains=self.q)

#         return qs.order_by('house__street__name', 'house__number', 'number')

#     def get_result_label(self, result):
#         """Форматирование строения для отображения."""
#         return f"{result.house.street}, д. {result.house.number}, стр. {result.number}"

# from django.db.models import Q
# class CoordinatesAutocomplete(autocomplete.Select2QuerySetView):
#     """
#     АВТОКОМПЛИТ ДЛЯ КООРДИНАТ.

#     ОСОБЕННОСТИ:
#         • Поиск по широте и долготе одновременно
#         • Поддержка частичного совпадения значений координат
#         • Отображение в формате "Широта: X, Долгота: Y"

#     ИСПОЛЬЗУЕТСЯ В:
#         • Административном интерфейсе для выбора координат
#         • Формах создания/редактирования адресов с геолокацией

#     ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:
#         • Поиск по "55.7" найдет координаты с широтой или долготой содержащей "55.7"
#         • Отображение: "Широта: 55.7558, Долгота: 37.6173"
#     """

#     def get_queryset(self):
#         """
#         ПОЛУЧЕНИЕ QUERYSET ДЛЯ КООРДИНАТ.

#         ЛОГИКА:
#             1. Начинаем со всех координат
#             2. Фильтруем по поисковому запросу в обоих полях (широта и долгота)
#             3. Сортируем по широте, затем по долготе

#         ВОЗВРАЩАЕТ:
#             QuerySet: Отфильтрованный queryset координат
#         """
#         qs = Coordinates.objects.all()

#         # Поиск по координатам
#         if self.q:
#             # Ищем в обоих полях
#             qs = qs.filter(
#                 Q(latitude__icontains=self.q) |
#                 Q(longitude__icontains=self.q)
#             )

#         return qs.order_by('latitude', 'longitude')

#     def get_result_label(self, result):
#         """
#         ФОРМАТИРОВАНИЕ КООРДИНАТ ДЛЯ ОТОБРАЖЕНИЯ.

#         АРГУМЕНТЫ:
#             result : Coordinates
#                 Объект координат

#         ВОЗВРАЩАЕТ:
#             str: Отформатированные координаты для пользовательского интерфейса
#         """
#         return f"Широта: {result.latitude}, Долгота: {result.longitude}"

# # ====================================================================================
# # МОДУЛЬ 2: КЛАССЫ ФИЛЬТРОВ ДЛЯ АДМИНКИ
# # ====================================================================================

# class CountryFilter(SimpleListFilter):
#     """
#     ФИЛЬТР ПО СТРАНЕ для связанных моделей.

#     ИСПОЛЬЗУЕТСЯ В:
#         • Федеральных округах
#         • Регионах
#         • Городах
#         • Адресах
#         • Координатах (через связь с адресами)

#     ОСОБЕННОСТИ:
#         • Универсальный фильтр для всей адресной иерархии
#         • Автоматически определяет связь с Country в разных моделях
#         • Поддерживает фильтрацию через несколько уровней вложенности
#     """

#     title = 'Страна'
#     parameter_name = 'country'

#     def lookups(self, request, model_admin):
#         """
#         ВОЗВРАЩАЕТ СПИСОК ВАРИАНТОВ ДЛЯ ФИЛЬТРА.

#         ВОЗВРАЩАЕТ:
#             list: Список кортежей (id, name) стран
#         """
#         countries = Country.objects.all().order_by('name')
#         return [(country.id, country.name) for country in countries]

#     def queryset(self, request, queryset):
#         """
#         ФИЛЬТРАЦИЯ QUERYSET ПО ВЫБРАННОЙ СТРАНЕ.

#         ЛОГИКА:
#             Определяет путь до Country в зависимости от модели:
#             • Прямая связь (Country)
#             • Через FederalDistrict
#             • Через Region → FederalDistrict
#             • Через City → Region → FederalDistrict
#             • Через Street → City → Region → FederalDistrict

#         ВОЗВРАЩАЕТ:
#             QuerySet: Отфильтрованный queryset по выбранной стране
#         """
#         if self.value():
#             # Для каждой модели свой способ фильтрации по стране
#             if hasattr(queryset.model, 'country'):
#                 return queryset.filter(country_id=self.value())
#             elif hasattr(queryset.model, 'federal_district'):
#                 return queryset.filter(federal_district__country_id=self.value())
#             elif hasattr(queryset.model, 'region'):
#                 return queryset.filter(region__federal_district__country_id=self.value())
#             elif hasattr(queryset.model, 'city'):
#                 return queryset.filter(city__region__federal_district__country_id=self.value())
#             elif hasattr(queryset.model, 'street'):
#                 return queryset.filter(street__city__region__federal_district__country_id=self.value())
#         return queryset


# class RegionFilter(SimpleListFilter):
#     """
#     ФИЛЬТР ПО РЕГИОНУ.

#     ОСОБЕННОСТИ:
#         • Фильтрация по региону для связанных моделей
#         • Поддерживает фильтрацию через City и Street
#         • Использует строковое представление региона для отображения
#     """

#     title = 'Регион'
#     parameter_name = 'region'

#     def lookups(self, request, model_admin):
#         """
#         ВОЗВРАЩАЕТ СПИСОК РЕГИОНОВ ДЛЯ ФИЛЬТРА.

#         Использует строковое представление региона (с типом) для удобства пользователя.
#         """

#         regions = Region.objects.all().order_by('name')
#         return [(region.id, str(region)) for region in regions]

#     def queryset(self, request, queryset):
#         """
#         ФИЛЬТРАЦИЯ ПО ВЫБРАННОМУ РЕГИОНУ.

#         ЛОГИКА:
#             • Прямая связь с Region
#             • Через City
#             • Через Street → City
#         """
#         if self.value():
#             if hasattr(queryset.model, 'region'):
#                 return queryset.filter(region_id=self.value())
#             elif hasattr(queryset.model, 'city'):
#                 return queryset.filter(city__region_id=self.value())
#             elif hasattr(queryset.model, 'street'):
#                 return queryset.filter(street__city__region_id=self.value())
#         return queryset


# class CityFilter(SimpleListFilter):
#     """
#     ФИЛЬТР ПО ГОРОДУ.

#     ОСОБЕННОСТИ:
#         • Фильтрация по городу для связанных моделей
#         • Поддерживает фильтрацию через Street
#         • Использует строковое представление города (с типом населенного пункта)
#     """

#     title = 'Город'
#     parameter_name = 'city'

#     def lookups(self, request, model_admin):
#         cities = City.objects.all().order_by('name')
#         return [(city.id, str(city)) for city in cities]

#     def queryset(self, request, queryset):
#         """
#         ФИЛЬТРАЦИЯ ПО ВЫБРАННОМУ ГОРОДУ.

#         ЛОГИКА:
#             • Прямая связь с City
#             • Через Street
#         """

#         if self.value():
#             if hasattr(queryset.model, 'city'):
#                 return queryset.filter(city_id=self.value())
#             elif hasattr(queryset.model, 'street'):
#                 return queryset.filter(street__city_id=self.value())
#         return queryset


# # ====================================================================================
# # МОДУЛЬ 3: КЛАССЫ MODELADMIN ДЛЯ ВСЕХ МОДЕЛЕЙ
# # ====================================================================================

# @admin.register(Country)
# class CountryAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ СТРАНАМИ.

#     НАСТРОЙКИ:
#         • Отображение: название страны
#         • Поиск: по названию страны
#         • Сортировка: по названию
#         • Фильтры: нет

#     ОСОБЕННОСТИ:
#         • Базовая модель, не имеет зависимостей
#         • Простой интерфейс управления
#     """

#     list_display = ('name',)
#     search_fields = ('name',)
#     ordering = ('name',)

#     # GIN индексы уже созданы в модели
#     # Django автоматически использует их для поиска


# @admin.register(FederalDistrict)
# class FederalDistrictAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ФЕДЕРАЛЬНЫМИ ОКРУГАМИ.

#     НАСТРОЙКИ:
#         • Отображение: название, сокращение, страна
#         • Поиск: по названию и сокращению
#         • Фильтры: по стране
#         • Autocomplete: для поля country

#     ОСОБЕННОСТИ:
#         • Использует autocomplete для выбора страны
#         • Фильтрация по стране
#         • Отображение связанной страны
#     """

#     list_display = ('name', 'abbreviated_name', 'country')
#     search_fields = ('name', 'abbreviated_name')
#     list_filter = (CountryFilter,)
#     autocomplete_fields = ('country',)
#     ordering = ('country__name', 'name')

#     def get_queryset(self, request):
#         """Оптимизация запроса с select_related."""
#         return super().get_queryset(request).select_related('country')


# @admin.register(TypeRegion)
# class TypeRegionAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ТИПАМИ РЕГИОНОВ.

#     НАСТРОЙКИ:
#         • Отображение: название, сокращение, правила отображения
#         • Поиск: по названию и сокращению
#         • Фильтры: по правилам отображения
#     """

#     list_display = ('name', 'abbreviated_name', 'show_before_name', 'skip_in_name')
#     search_fields = ('name', 'abbreviated_name')
#     list_filter = ('show_before_name', 'skip_in_name')
#     ordering = ('name',)


# @admin.register(Timezone)
# class TimezoneAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ЧАСОВЫМИ ПОЯСАМИ.

#     НАСТРОЙКИ:
#         • Отображение: название, смещения UTC и Москвы
#         • Поиск: по названию
#         • Сортировка: по смещению UTC
#     """

#     list_display = ('name', 'offset_utc', 'offset_moscow')
#     search_fields = ('name',)
#     ordering = ('offset_utc', 'name')

#     def offset_utc(self, obj):
#         """Форматирование смещения UTC."""
#         return f"UTC{obj.offset_utc:+d}"

#     def offset_moscow(self, obj):
#         """Форматирование смещения относительно Москвы."""
#         return f"МСК{obj.offset_moscow:+d}"

#     offset_utc.short_description = 'Смещение UTC'
#     offset_moscow.short_description = 'Смещение МСК'


# @admin.register(Region)
# class RegionAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ РЕГИОНАМИ.

#     НАСТРОЙКИ:
#         • Отображение: название, тип, федеральный округ
#         • Поиск: по названию и сокращению
#         • Фильтры: по федеральному округу, типу региона, часовому поясу
#         • Autocomplete: для всех связанных полей

#     ОСОБЕННОСТИ:
#         • Использует autocomplete для зависимых полей
#         • Отображает форматированное название региона
#         • Поддерживает фильтрацию по всем связанным моделям
#     """

#     list_display = ('get_display_name', 'type_region', 'federal_district', 'timezone')
#     search_fields = ('name', 'abbreviated_name')
#     list_filter = ('federal_district', 'type_region', 'timezone')
#     autocomplete_fields = ('federal_district', 'type_region', 'timezone')
#     ordering = ('federal_district__name', 'name')

#     def get_display_name(self, obj):
#         """Форматированное название региона для отображения."""
#         return str(obj)

#     get_display_name.short_description = 'Регион'
#     get_display_name.admin_order_field = 'name'

#     def get_queryset(self, request):
#         """Оптимизация запроса с select_related."""
#         return super().get_queryset(request).select_related(
#             'federal_district', 'type_region', 'timezone'
#         )


# @admin.register(LocalityType)
# class LocalityTypeAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ТИПАМИ НАСЕЛЕННЫХ ПУНКТОВ.

#     НАСТРОЙКИ:
#         • Отображение: название, сокращение, правила отображения
#         • Поиск: по названию и сокращению
#         • Фильтры: по наличию административных округов
#     """

#     list_display = ('name', 'abbreviated_name', 'show_before_name', 'has_administrative_territory')
#     search_fields = ('name', 'abbreviated_name')
#     list_filter = ('show_before_name', 'has_administrative_territory')
#     ordering = ('name',)


# @admin.register(City)
# class CityAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ГОРОДАМИ.

#     НАСТРОЙКИ:
#         • Отображение: название, тип, регион
#         • Поиск: по названию города
#         • Фильтры: по региону, типу населенного пункта, часовому поясу
#         • Autocomplete: для всех связанных полей
#     """

#     list_display = ('get_display_name', 'locality_type', 'region', 'timezone')
#     search_fields = ('name',)
#     list_filter = (RegionFilter, 'locality_type', 'timezone', 'has_administrative_territory')
#     autocomplete_fields = ('region', 'locality_type', 'timezone')
#     ordering = ('region__name', 'name')

#     def get_display_name(self, obj):
#         """Форматированное название города для отображения."""
#         return str(obj)

#     get_display_name.short_description = 'Город'
#     get_display_name.admin_order_field = 'name'

#     def get_queryset(self, request):
#         """Оптимизация запроса с select_related."""
#         return super().get_queryset(request).select_related(
#             'region', 'locality_type', 'timezone'
#         )


# @admin.register(AdministrativeTerritory)
# class AdministrativeTerritoryAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ АДМИНИСТРАТИВНЫМИ ОКРУГАМИ.

#     НАСТРОЙКИ:
#         • Отображение: название, город
#         • Поиск: по названию округа
#         • Фильтры: по городу
#         • Autocomplete: для поля city
#     """

#     list_display = ('name', 'city')
#     search_fields = ('name',)
#     list_filter = (CityFilter,)
#     autocomplete_fields = ('city',)
#     ordering = ('city__name', 'name')

#     def get_queryset(self, request):
#         """Оптимизация запроса с select_related."""
#         return super().get_queryset(request).select_related('city')


# @admin.register(AdministrativeTerritorialUnit)
# class AdministrativeUnitAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ АДМИНИСТРАТИВНО-ТЕРРИТОРИАЛЬНЫМИ ЕДИНИЦАМИ.

#     НАСТРОЙКИ:
#         • Отображение: название, город, административный округ
#         • Поиск: по названию АТЕ
#         • Фильтры: по городу, административному округу
#         • Autocomplete: для всех связанных полей
#     """

#     list_display = ('name', 'city', 'administrative_territory')
#     search_fields = ('name',)
#     list_filter = (CityFilter, 'administrative_territory')
#     autocomplete_fields = ('city', 'administrative_territory')
#     ordering = ('city__name', 'name')

#     def get_queryset(self, request):
#         """Оптимизация запроса с select_related."""
#         return super().get_queryset(request).select_related(
#             'city', 'administrative_territory'
#         )


# @admin.register(StreetType)
# class StreetTypeAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ТИПАМИ УЛИЦ.

#     НАСТРОЙКИ:
#         • Отображение: название, сокращение, правило отображения
#         • Поиск: по названию и сокращению
#         • Фильтры: по правилу отображения
#     """

#     list_display = ('name', 'abbreviated_name', 'show_before_name')
#     search_fields = ('name', 'abbreviated_name')
#     list_filter = ('show_before_name',)
#     ordering = ('name',)


# @admin.register(Street)
# class StreetAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ УЛИЦАМИ.

#     НАСТРОЙКИ:
#         • Отображение: название, тип, город
#         • Поиск: по названию улицы
#         • Фильтры: по городу, типу улицы
#         • Autocomplete: для всех связанных полей
#     """

#     list_display = ('get_display_name', 'street_type', 'city')
#     search_fields = ('name',)
#     list_filter = (CityFilter, 'street_type')
#     autocomplete_fields = ('city', 'street_type')
#     ordering = ('city__name', 'name')

#     def get_display_name(self, obj):
#         """Форматированное название улицы для отображения."""
#         return str(obj)

#     get_display_name.short_description = 'Улица'
#     get_display_name.admin_order_field = 'name'

#     def get_queryset(self, request):
#         """Оптимизация запроса с select_related."""
#         return super().get_queryset(request).select_related('city', 'street_type')


# @admin.register(House)
# class HouseAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ДОМАМИ.

#     НАСТРОЙКИ:
#         • Отображение: номер, улица, город
#         • Поиск: по номеру дома
#         • Фильтры: по улице
#         • Autocomplete: для поля street
#     """

#     list_display = ('number', 'street', 'get_city')
#     search_fields = ('number',)
#     list_filter = ('street',)
#     autocomplete_fields = ('street',)
#     ordering = ('street__name', 'number')

#     def get_city(self, obj):
#         """Город для отображения (вычисляемое поле)."""
#         return obj.street.city

#     get_city.short_description = 'Город'
#     get_city.admin_order_field = 'street__city__name'

#     def get_queryset(self, request):
#         """Оптимизация запроса с select_related."""
#         return super().get_queryset(request).select_related('street', 'street__city')


# @admin.register(Building)
# class BuildingAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ СТРОЕНИЯМИ.

#     НАСТРОЙКИ:
#         • Отображение: номер, дом, улица
#         • Поиск: по номеру строения
#         • Фильтры: по дому
#         • Autocomplete: для поля house
#     """

#     list_display = ('number', 'house', 'get_street', 'get_city')
#     search_fields = ('number',)
#     list_filter = ('house',)
#     autocomplete_fields = ('house',)
#     ordering = ('house__street__name', 'house__number', 'number')

#     def get_street(self, obj):
#         """Улица для отображения (вычисляемое поле)."""
#         return obj.house.street

#     def get_city(self, obj):
#         """Город для отображения (вычисляемое поле)."""
#         return obj.house.street.city

#     get_street.short_description = 'Улица'
#     get_street.admin_order_field = 'house__street__name'

#     get_city.short_description = 'Город'
#     get_city.admin_order_field = 'house__street__city__name'

#     def get_queryset(self, request):
#         """Оптимизация запроса с select_related."""
#         return super().get_queryset(request).select_related(
#             'house', 'house__street', 'house__street__city'
#         )

# @admin.register(Coordinates)
# class CoordinatesAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ Координатами.

#     НАСТРОЙКИ:
#         • Отображение: название, сокращение, правило отображения
#         • Поиск: по названию и сокращению
#         • Фильтры: по правилу отображения
#     """

#     list_display = ('latitude', 'longitude')
#     search_fields = ('latitude', 'longitude')
#     list_filter = ('latitude', 'longitude')
#     ordering = ('latitude', 'longitude')

# @admin.register(Address)
# class AddressAdmin(admin.ModelAdmin):
#     """
#     АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ АДРЕСАМИ.

#     НАСТРОЙКИ:
#         • Отображение: полный адрес, страна, регион, город, улица, дом, строение, индекс
#         • Поиск: по всем компонентам адреса
#         • Фильтры: по всем связанным моделям
#         • Autocomplete: для всех связанных полей
#         • Readonly: вычисляемое поле full_address

#     ОСОБЕННОСТИ:
#         • Отображает полный адрес в удобном формате
#         • Поддерживает сложную фильтрацию по всем компонентам
#         • Использует autocomplete для улучшения UX
#         • Оптимизированные запросы с select_related
#     """

#     # Поля для отображения в списке
#     list_display = (
#         'full_address_display',
#         'country',
#         'region',
#         'city',
#         'street',
#         'house',
#         'building',
#         'coordinates',
#         'index'
#     )

#     # Поля для поиска
#     search_fields = (
#         'country__name',
#         'region__name',
#         'city__name',
#         'administrative_territory__name',
#         'administrative_unit__name',
#         'street__name',
#         'house__number',
#         'building__number',
#         'microdistrict',
#         'index'
#     )

#     # Фильтры
#     list_filter = (
#         CountryFilter,
#         'federal_district',
#         RegionFilter,
#         CityFilter,
#         'administrative_territory',
#         'administrative_unit',
#         'street',
#         'house',
#         'building',
#     )

#     # Поля с autocomplete
#     autocomplete_fields = (
#         'country',
#         'federal_district',
#         'region',
#         'city',
#         'administrative_territory',
#         'administrative_unit',
#         'street',
#         'house',
#         'building',
#         'coordinates',
#     )

#     # Только для чтения
#     readonly_fields = ('full_address',)

#     # Сортировка
#     ordering = (
#         'country__name',
#         'region__name',
#         'city__name',
#         'street__name',
#         'house__number',
#         'building__number'
#     )

#     # Группировка полей в форме
#     fieldsets = (
#         ('Основная информация', {
#             'fields': (
#                 'country',
#                 'federal_district',
#                 'region',
#                 'city',
#                 'full_address'
#             )
#         }),
#         ('Административное деление', {
#             'fields': (
#                 'administrative_territory',
#                 'administrative_unit',
#             ),
#             'classes': ('collapse',)
#         }),
#         ('Улично-домовая сеть', {
#             'fields': (
#                 'street',
#                 'house',
#                 'building',
#             )
#         }),
#         ('Координаты', {
#             'fields': (
#                 'coordinates',
#             )
#         }),

#         ('Дополнительная информация', {
#             'fields': (
#                 'microdistrict',
#                 'index',
#             ),
#             'classes': ('collapse',)
#         }),
#     )

#     def full_address_display(self, obj):
#         """
#         ОТОБРАЖЕНИЕ ПОЛНОГО АДРЕСА В СПИСКЕ.

#         АРГУМЕНТЫ:
#             obj : Address
#                 Объект адреса

#         ВОЗВРАЩАЕТ:
#             str: Отформатированный полный адрес
#         """
#         return obj.full_address

#     full_address_display.short_description = 'Полный адрес'
#     full_address_display.admin_order_field = 'city__name'

#     def get_queryset(self, request):
#         """
#         ОПТИМИЗАЦИЯ ЗАПРОСА ДЛЯ АДРЕСОВ.

#         ИСПОЛЬЗУЕТ select_related для всех связанных моделей
#         чтобы избежать N+1 проблем при отображении списка.
#         """
#         return super().get_queryset(request).select_related(
#             'country',
#             'federal_district',
#             'region',
#             'city',
#             'administrative_territory',
#             'administrative_unit',
#             'street',
#             'house',
#             'building',
#             'coordinates',
#         )

#     def save_model(self, request, obj, form, change):
#         """
#         СОХРАНЕНИЕ МОДЕЛИ АДРЕСА С ДОПОЛНИТЕЛЬНОЙ ОБРАБОТКОЙ.

#         ДЕЙСТВИЯ:
#             1. Автоматическое заполнение недостающих полей из иерархии
#             2. Проверка существования такого же адреса
#             3. Вызов родительского метода сохранения

#         АРГУМЕНТЫ:
#             request : HttpRequest
#                 Запрос

#             obj : Address
#                 Объект адреса

#             form : Form
#                 Форма

#             change : bool
#                 Флаг изменения (True) или создания (False)
#         """
#         # Автоматически заполняем недостающие поля из иерархии
#         if obj.region and not obj.country:
#             obj.country = obj.region.federal_district.country

#         if obj.region and not obj.federal_district:
#             obj.federal_district = obj.region.federal_district

#         if obj.city and not obj.region:
#             obj.region = obj.city.region

#         if obj.street and not obj.city:
#             obj.city = obj.street.city

#         if obj.house and not obj.street:
#             obj.street = obj.house.street

#         if obj.building and not obj.house:
#             obj.house = obj.building.house

#         # Проверяем существование такого же адреса
#         if not change:  # Только при создании
#             existing = obj._find_existing_address()
#             if existing:
#                 # Если нашли существующий, можно показать сообщение
#                 # или выполнить другие действия
#                 pass

#         super().save_model(request, obj, form, change)

#     def full_address(self, obj):
#         """
#         ОТОБРАЖЕНИЕ ПОЛНОГО АДРЕСА В ФОРМЕ РЕДАКТИРОВАНИЯ.

#         АРГУМЕНТЫ:
#             obj : Address
#                 Объект адреса

#         ВОЗВРАЩАЕТ:
#             str: Отформатированный полный адрес
#         """
#         return format_html('<strong>{}</strong>', obj.full_address)

#     full_address.short_description = 'Полный адрес (автоматически)'