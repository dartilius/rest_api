"""
URL конфигурация для справочника адресов.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CountryViewSet,
    FederalDistrictViewSet,
    TypeRegionViewSet,
    TimezoneViewSet,
    RegionViewSet,
    LocalityTypeViewSet,
    CityViewSet,
    AdministrativeTerritoryViewSet,
    AdministrativeTerritorialUnitViewSet,
    StreetTypeViewSet,
    StreetViewSet,
    HouseViewSet,
    BuildingViewSet,
    CoordinatesViewSet,
    AddressViewSet,
)

router = DefaultRouter()
router.trailing_slash = "/"

router.register("countries", CountryViewSet, basename="countries")
router.register(
    "federal-districts", FederalDistrictViewSet, basename="federal_districts"
)
router.register("type-regions", TypeRegionViewSet, basename="type_regions")
router.register("timezones", TimezoneViewSet, basename="timezones")
router.register("regions", RegionViewSet, basename="regions")
router.register("locality-types", LocalityTypeViewSet, basename="locality_types")
router.register("cities", CityViewSet, basename="cities")
router.register(
    "administrative-territories",
    AdministrativeTerritoryViewSet,
    basename="administrative_territories",
)
router.register(
    "administrative-units",
    AdministrativeTerritorialUnitViewSet,
    basename="administrative_units",
)
router.register("street-types", StreetTypeViewSet, basename="street_types")
router.register("streets", StreetViewSet, basename="streets")
router.register("houses", HouseViewSet, basename="houses")
router.register("buildings", BuildingViewSet, basename="buildings")
router.register("coordinates", CoordinatesViewSet, basename="coordinates")
router.register("addresses", AddressViewSet, basename="addresses")

urlpatterns = [
    path("", include(router.urls)),
]
