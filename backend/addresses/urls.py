from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import admin as addresses_admin  # импортируем autocomplete views из admin.py
from .views import (
    CountryViewSet, FederalDistrictViewSet, TypeRegionViewSet, TimezoneViewSet, RegionViewSet,
    LocalityTypeViewSet, CityViewSet, AdministrativeTerritoryViewSet,
    AdministrativeTerritorialUnitViewSet, StreetTypeViewSet, StreetViewSet,
    HouseViewSet, BuildingViewSet, AddressViewSet
)

# -------------------------------
# DRF Router — ViewSets
# -------------------------------
router = DefaultRouter()
router.register("countries", CountryViewSet, basename="countries")
router.register("federal-districts", FederalDistrictViewSet, basename="federal-districts")
router.register("type-regions", TypeRegionViewSet, basename="type-regions")
router.register("timezones", TimezoneViewSet, basename="timezones")
router.register("regions", RegionViewSet, basename="regions")
router.register("locality-types", LocalityTypeViewSet, basename="locality-types")
router.register("cities", CityViewSet, basename="cities")
router.register("administrative-territories", AdministrativeTerritoryViewSet, basename="administrative-territories")
router.register("administrative-territorial-units", AdministrativeTerritorialUnitViewSet, basename="administrative-territorial-units")
router.register("street-types", StreetTypeViewSet, basename="street-types")
router.register("streets", StreetViewSet, basename="streets")
router.register("houses", HouseViewSet, basename="houses")
router.register("buildings", BuildingViewSet, basename="buildings")
router.register("addresses", AddressViewSet, basename="addresses")

# -------------------------------
# Autocomplete (DAL)
# -------------------------------
urlpatterns = [
    path("", include(router.urls)),

    path("autocomplete/federal-district/", addresses_admin.FederalDistrictAutocomplete.as_view(), name="federal-district-autocomplete"),
    path("autocomplete/region/", addresses_admin.RegionAutocomplete.as_view(), name="region-autocomplete"),
    path("autocomplete/city/", addresses_admin.CityAutocomplete.as_view(), name="city-autocomplete"),
    path("autocomplete/administrative-territory/", addresses_admin.AdministrativeTerritoryAutocomplete.as_view(), name="administrative-territory-autocomplete"),
    path("autocomplete/administrative-unit/", addresses_admin.AdministrativeUnitAutocomplete.as_view(), name="administrative-unit-autocomplete"),
    path("autocomplete/street/", addresses_admin.StreetAutocomplete.as_view(), name="street-autocomplete"),
    path("autocomplete/house/", addresses_admin.HouseAutocomplete.as_view(), name="house-autocomplete"),
    path("autocomplete/building/", addresses_admin.BuildingAutocomplete.as_view(), name="building-autocomplete"),
]
