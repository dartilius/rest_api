from django.contrib import admin
from dal import autocomplete
from .models import (
    Country, FederalDistrict, TypeRegion, Timezone, Region,
    LocalityType, City, AdministrativeTerritory,
    AdministrativeTerritorialUnit, StreetType, Street,
    House, Building, Address
)

# ===============================
#  Autocomplete Views
# ===============================

class FederalDistrictAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = FederalDistrict.objects.all()
        country_id = self.forwarded.get('country', None)
        if country_id:
            qs = qs.filter(country_id=country_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class RegionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Region.objects.all()
        fd_id = self.forwarded.get('federal_district', None)
        if fd_id:
            qs = qs.filter(federal_district_id=fd_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class CityAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = City.objects.all()
        region_id = self.forwarded.get('region', None)
        if region_id:
            qs = qs.filter(region_id=region_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class AdministrativeTerritoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = AdministrativeTerritory.objects.all()
        city_id = self.forwarded.get('city', None)
        if city_id:
            qs = qs.filter(city_id=city_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class AdministrativeUnitAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = AdministrativeTerritorialUnit.objects.all()
        city_id = self.forwarded.get('city', None)
        if city_id:
            qs = qs.filter(city_id=city_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class StreetAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Street.objects.all()
        city_id = self.forwarded.get('city', None)
        if city_id:
            qs = qs.filter(city_id=city_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class HouseAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = House.objects.all()
        street_id = self.forwarded.get('street', None)
        if street_id:
            qs = qs.filter(street_id=street_id)
        if self.q:
            qs = qs.filter(number__icontains=self.q)
        return qs


class BuildingAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Building.objects.all()
        house_id = self.forwarded.get('house', None)
        if house_id:
            qs = qs.filter(house_id=house_id)
        if self.q:
            qs = qs.filter(number__icontains=self.q)
        return qs


# ===============================
#  ModelAdmin настройки
# ===============================

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(FederalDistrict)
class FederalDistrictAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    autocomplete_fields = ('country',)


@admin.register(TypeRegion)
class TypeRegionAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Timezone)
class TimezoneAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    autocomplete_fields = ('federal_district', 'type_region', 'timezone')
    ordering = ('federal_district__name', 'name')


@admin.register(LocalityType)
class LocalityTypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    autocomplete_fields = ('region', 'locality_type', 'timezone')
    ordering = ('region__name', 'name')


@admin.register(AdministrativeTerritory)
class AdministrativeTerritoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    autocomplete_fields = ('city',)


@admin.register(AdministrativeTerritorialUnit)
class AdministrativeUnitAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    autocomplete_fields = ('city', 'administrative_territory')


@admin.register(StreetType)
class StreetTypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    autocomplete_fields = ('city', 'street_type')
    ordering = ('city__name', 'name')


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    search_fields = ('number',)
    autocomplete_fields = ('street',)
    ordering = ('street__city__region__federal_district__name', 'street__city__name', 'street__name', 'number')


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    search_fields = ('number',)
    autocomplete_fields = ('house',)
    ordering = ('house__street__city__region__name', 'house__street__name', 'house__number', 'number')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        'code1c', 'full_address', 'country', 'federal_district', 'region',
        'city', 'street', 'house', 'building', 'index'
    )
    search_fields = ('code1c', 'street__name', 'house__number', 'building__number', 'city__name', 'region__name')
    autocomplete_fields = (
        'country', 'federal_district', 'region', 'city',
        'administrative_territory', 'administrative_unit',
        'street', 'house', 'building'
    )
    readonly_fields = ('full_address',)
    ordering = ('country__name', 'region__name', 'city__name', 'street__name', 'house__number', 'building__number')

    def full_address(self, obj):
        return obj.full_address
