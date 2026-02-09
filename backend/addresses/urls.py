"""
URL конфигурация для справочника адресов.

МОДУЛЬ URLS:
─────────────────────────────────────────────────────────────────────────────────────
Этот модуль определяет все URL маршруты для работы с адресами через:
1. Django REST Framework (API)
2. Django Autocomplete Light (автокомплит для админки)

СТРУКТУРА МАРШРУТОВ:
─────────────────────────────────────────────────────────────────────────────────────
/api/addresses/
├── countries/                    - Страны
├── federal-districts/            - Федеральные округа
├── type-regions/                 - Типы регионов
├── timezones/                    - Часовые пояса
├── regions/                      - Регионы
├── locality-types/               - Типы населенных пунктов
├── cities/                       - Города
├── administrative-territories/   - Административные округа
├── administrative-territorial-units/ - Административно-территориальные единицы
├── street-types/                 - Типы улиц
├── streets/                      - Улицы
├── houses/                       - Дома
├── buildings/                    - Строения
├── addresses/                    - Полные адресы
│   ├── search/                   - Поиск адресов
│   ├── bulk_create/              - Массовое создание
│   ├── create_by_uuid/           - Создание по UUID
│   └── statistics/               - Статистика
└── autocomplete/
    ├── federal-district/         - Автокомплит федеральных округов
    ├── region/                   - Автокомплит регионов
    ├── city/                     - Автокомплит городов
    ├── administrative-territory/ - Автокомплит административных округов
    ├── administrative-unit/      - Автокомплит административных единиц
    ├── street/                   - Автокомплит улиц
    ├── house/                    - Автокомплит домов
    └── building/                 - Автокомплит строений

ОСОБЕННОСТИ:
• Использование DefaultRouter для автоматической генерации URL
• Отдельные маршруты для автокомплита
• Поддержка всех CRUD операций через API
• Специальные эндпоинты для расширенной функциональности
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

# Импорт autocomplete views из admin.py
from . import admin as addresses_admin

# Импорт ViewSets
from .views import (
    CountryViewSet, FederalDistrictViewSet, TypeRegionViewSet,
    TimezoneViewSet, RegionViewSet, LocalityTypeViewSet,
    CityViewSet, AdministrativeTerritoryViewSet,
    AdministrativeTerritorialUnitViewSet, StreetTypeViewSet,
    StreetViewSet, HouseViewSet, BuildingViewSet, AddressViewSet, CoordinatesViewSet,
)


# ====================================================================================
# МОДУЛЬ 1: НАСТРОЙКА DRF ROUTER ДЛЯ ВСЕХ VIEWSETS
# ====================================================================================

# Создание основного роутера
router = DefaultRouter()
router.trailing_slash = '/'

# Регистрация всех ViewSets
router.register("countries", CountryViewSet, basename="countries")
router.register("federal-districts", FederalDistrictViewSet, basename="federal_districts")
router.register("type-regions", TypeRegionViewSet, basename="type_regions")
router.register("timezones", TimezoneViewSet, basename="timezones")
router.register("regions", RegionViewSet, basename="regions")
router.register("locality-types", LocalityTypeViewSet, basename="locality_types")
router.register("cities", CityViewSet, basename="cities")
router.register("administrative_territories", AdministrativeTerritoryViewSet,
                basename="administrative_territories")
router.register("administrative_territorial_units", AdministrativeTerritorialUnitViewSet,
                basename="administrative_territorial_units")
router.register("street_types", StreetTypeViewSet, basename="street_types")
router.register("streets", StreetViewSet, basename="streets")
router.register("houses", HouseViewSet, basename="houses")
router.register("buildings", BuildingViewSet, basename="buildings")
router.register("coordinates", CoordinatesViewSet, basename="coordinates")
router.register("addresses", AddressViewSet, basename="addresses")


# ====================================================================================
# МОДУЛЬ 2: URL ДЛЯ АВТОКОМПЛИТА (DAL)
# ====================================================================================

# URL для автокомплита (используются в админке и формах)
autocomplete_urlpatterns = [
    path(
        "federal_district/",
        addresses_admin.FederalDistrictAutocomplete.as_view(),
        name="federal_district-autocomplete"
    ),
    path(
        "region/",
        addresses_admin.RegionAutocomplete.as_view(),
        name="region_autocomplete"
    ),
    path(
        "city/",
        addresses_admin.CityAutocomplete.as_view(),
        name="city_autocomplete"
    ),
    path(
        "administrative_territory/",
        addresses_admin.AdministrativeTerritoryAutocomplete.as_view(),
        name="administrative_territory_autocomplete"
    ),
    path(
        "administrative_unit/",
        addresses_admin.AdministrativeUnitAutocomplete.as_view(),
        name="administrative_unit_autocomplete"
    ),
    path(
        "street/",
        addresses_admin.StreetAutocomplete.as_view(),
        name="street_autocomplete"
    ),
    path(
        "house/",
        addresses_admin.HouseAutocomplete.as_view(),
        name="house_autocomplete"
    ),
    path(
        "building/",
        addresses_admin.BuildingAutocomplete.as_view(),
        name="building_autocomplete"
    ),
    path(
        "coordinates/",
        addresses_admin.CoordinatesAutocomplete.as_view(),
        name="coordinates_autocomplete"
    ),
]


# ====================================================================================
# МОДУЛЬ 3: ОСНОВНЫЕ URL ПАТТЕРНЫ
# ====================================================================================

# Основные URL паттерны приложения
urlpatterns = [
    # API маршруты через DRF Router
    path("", include(router.urls)),

    # Автокомплит маршруты
    path("autocomplete/", include((autocomplete_urlpatterns, 'autocomplete'))),
]


# ====================================================================================
# МОДУЛЬ 4: ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ О МАРШРУТАХ
# ====================================================================================

"""
ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ О МАРШРУТАХ:

1. API МАРШРУТЫ (через DRF Router):
   Все маршруты поддерживают стандартные HTTP методы:
   • GET    - получение списка или деталей
   • POST   - создание нового объекта
   • PUT    - полное обновление объекта
   • PATCH  - частичное обновление объекта
   • DELETE - удаление объекта

2. СПЕЦИАЛЬНЫЕ ЭНДПОИНТЫ ДЛЯ АДРЕСОВ:
   • POST /api/addresses/addresses/search/      - расширенный поиск
   • POST /api/addresses/addresses/bulk_create/ - массовое создание
   • POST /api/addresses/addresses/create_by_uuid/ - создание по UUID
   • GET  /api/addresses/addresses/statistics/  - статистика

3. АВТОКОМПЛИТ МАРШРУТЫ:
   Используются Django Autocomplete Light для улучшения UX в:
   • Административном интерфейсе Django
   • Пользовательских формах с зависимыми полями
   Все автокомплит маршруты возвращают JSON для Select2

4. ПАГИНАЦИЯ И ФИЛЬТРАЦИЯ:
   Все списковые эндпоинты поддерживают:
   • Пагинацию: ?page=2&page_size=50
   • Поиск: ?search=Москва
   • Сортировку: ?ordering=name
   • Фильтрацию: ?country=uuid&region=uuid

ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:

1. Получение списка стран:
   GET /api/addresses/countries/

2. Поиск городов по названию:
   GET /api/addresses/cities/?search=Москва

3. Создание адреса с вложенной структурой:
   POST /api/addresses/addresses/
   Body: {
     "country": {"name": "Россия"},
     "city": {"name": "Москва"},
     "street": {"name": "Ленина"},
     "house": {"number": "1"}
   }

4. Поиск адресов:
   POST /api/addresses/addresses/search/
   Body: {
     "query": "Москва Ленина",
     "limit": 10
   }

5. Автокомплит улиц для города:
   GET /api/addresses/autocomplete/street/?q=Лен&city=uuid
"""