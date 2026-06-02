"""
Вьюсеты (ViewSets) для справочника адресов с упрощённой фильтрацией.

МОДУЛЬ VIEWSETS:
─────────────────────────────────────────────────────────────────────────────────────
Все ViewSets поддерживают единые параметры фильтрации и пагинации.

СТРУКТУРА ОТВЕТА БЕЗ ПАГИНАЦИИ:
{
    "count": 1250,
    "results": [... все записи ...]
}

СТРУКТУРА ОТВЕТА С ПАГИНАЦИЕЙ (?page=2):
{
    "count": 1250,
    "next": "http://api/addresses/?page=3&limit=100",
    "previous": "http://api/addresses/?page=1&limit=100",
    "results": [... записи страницы 2 ...]
}

📌 ЕДИНЫЕ ПАРАМЕТРЫ ФИЛЬТРАЦИИ:
• search - текстовый поиск
• ids - фильтр по ID через запятую (uuid1,uuid2,uuid3)
• ordering - сортировка (name, -name, city__name)
• page - номер страницы (включает пагинацию)
• limit - размер страницы (работает только с ?page=)

📌 ОСОБЕННОСТИ:
• Пагинация отключена по умолчанию
• ?page= включает пагинацию с размером 100
• ?limit= меняет размер страницы при наличии ?page=
• Все ViewSets используют единый стиль фильтрации
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema

from api.pagination import CustomLimitOffsetPagination
from .models import (
    Country, FederalDistrict, TypeRegion, Timezone, Region,
    LocalityType, City, AdministrativeTerritory,
    AdministrativeTerritorialUnit, StreetType, Street,
    House, Building, Address, Coordinates
)
from .serializers import (
    CountrySerializer, FederalDistrictSerializer, TypeRegionSerializer,
    TimezoneSerializer, RegionSerializer, LocalityTypeSerializer,
    CitySerializer, AdministrativeTerritorySerializer,
    AdministrativeUnitSerializer, StreetTypeSerializer,
    StreetSerializer, HouseSerializer, BuildingSerializer,
    AddressReadSerializer, AddressCreateSerializer, CoordinatesSerializers
)
from .filters import (
    CountryFilter, RegionFilter, CityFilter, StreetFilter, AddressFilter
)
from .schemas import (
    country_list_schema,
    city_list_schema, street_list_schema
)


# ====================================================================================
# МОДУЛЬ 1: КЛАСС ПАГИНАЦИИ, КОТОРЫЙ РАБОТАЕТ ТОЛЬКО С ПАРАМЕТРОМ ?page=
# ====================================================================================

class OptionalPagination(PageNumberPagination):
    """
    ПАГИНАЦИЯ, КОТОРАЯ ВКЛЮЧАЕТСЯ ТОЛЬКО ПРИ УКАЗАНИИ ПАРАМЕТРА ?page=

    📌 ЕДИНЫЙ СТАНДАРТ ПАРАМЕТРОВ:
    • page - номер страницы (включает пагинацию)
    • limit - размер страницы (работает только с ?page=)

    ПОВЕДЕНИЕ:
    1. Без параметров → возвращаются ВСЕ данные
    2. С параметром ?page= → включается пагинация
    3. С параметрами ?page= и ?limit= → пагинация с указанным размером

    ПРИМЕРЫ:
    • GET /api/addresses/addresses/ → все адреса
    • GET /api/addresses/addresses/?page=2 → пагинация (страница 2, размер 100)
    • GET /api/addresses/addresses/?page=1&limit=50 → страница 1, 50 записей
    • GET /api/addresses/addresses/?search=Москва → все адреса Москвы (без пагинации)

    ОГРАНИЧЕНИЯ:
    • Максимальный размер страницы: 1000 записей
    • Минимальный размер страницы: 1 запись
    """

    page_size = 100  # Размер страницы по умолчанию при включении пагинации
    page_size_query_param = 'limit'
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        """
        ВКЛЮЧАЕМ ПАГИНАЦИЮ ТОЛЬКО ЕСЛИ УКАЗАН ПАРАМЕТР ?page=

        ЛОГИКА:
        1. Если есть параметр ?page= → включаем пагинацию
        2. Если нет параметра ?page= → возвращаем None (все данные)
        3. Размер страницы берется из ?limit= или используем page_size
        """
        page = request.query_params.get(self.page_query_param)

        if page is not None:
            # Включаем пагинацию
            self.page_size = self.get_page_size(request)
            return super().paginate_queryset(queryset, request, view)

        # Пагинация не требуется - возвращаем все данные
        return None

    def get_paginated_response(self, data):
        """
        ФОРМИРУЕМ ОТВЕТ В ЗАВИСИМОСТИ ОТ ТОГО, ИСПОЛЬЗУЕТСЯ ЛИ ПАГИНАЦИЯ.

        БЕЗ ПАГИНАЦИИ:
        {
            "count": 1250,
            "results": [... все записи ...]
        }

        С ПАГИНАЦИЕЙ:
        {
            "count": 1250,
            "next": "https://.../?page=3&limit=100",
            "previous": "http://.../?page=1&limit=100",
            "results": [... записи страницы ...]
        }
        """

        if self.page is None:
            # Без пагинации - возвращаем просто список
            return Response({
                'count': len(data),
                'results': data
            })

        # С пагинацией - стандартный ответ DRF
        return super().get_paginated_response(data)

    def get_page_size(self, request):
        """
        ПОЛУЧЕНИЕ РАЗМЕРА СТРАНИЦЫ.

        ЛОГИКА:
        1. Если указан ?limit= → используем его
        2. Если не указан → используем page_size по умолчанию
        3. Ограничиваем максимальным размером max_page_size
        """
        if self.page_size_query_param:
            try:
                page_size = int(request.query_params.get(self.page_size_query_param, self.page_size))
                return min(page_size, self.max_page_size)
            except (ValueError, TypeError):
                pass

        return self.page_size


# ====================================================================================
# МОДУЛЬ 2: БАЗОВЫЕ VIEWSETS ДЛЯ ВСЕХ МОДЕЛЕЙ
# ====================================================================================

@extend_schema(
    tags=["Страны"],
    description="""
    Управление странами.
    
    📌 ПАРАМЕТРЫ ФИЛЬТРАЦИИ:
    • search - поиск по названию страны
    • ids - фильтр по ID через запятую (uuid1,uuid2)
    • ordering - сортировка (name, -name)
    • page - номер страницы (включает пагинацию)
    • limit - размер страницы (только с ?page=)

    ПРИМЕРЫ:
    • GET /api/addresses/countries/ → все страны
    • GET /api/addresses/countries/?q=Рос → поиск стран с "Рос"
    • GET /api/addresses/countries/?page=2 → страница 2 (пагинация)
    • GET /api/addresses/countries/?ids=uuid1,uuid2 → фильтр по ID
    • GET /api/addresses/countries/?page=1&limit=20 → страница 1, 20 записей
    """
)
class CountryViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ СТРАНАМИ.

    📌 ФИЛЬТРАЦИЯ:
    • Единый стиль фильтрации (search, ids, ordering)
    • Пагинация только при ?page=
    """
    queryset = Country.objects.all().order_by('name')
    serializer_class = CountrySerializer
    pagination_class = OptionalPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]  # обращение к глобальному фильтру
    filterset_class = CountryFilter  # логика фильтра для стран
    ordering = ['name']  # Дефолтная сортировка

    @country_list_schema()
    def list(self, request, *args, **kwargs):
        """Список стран."""
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["Федеральные округа"],
    description = """
    Управление федеральными округами (только для России)

    📌 ПАРАМЕТРЫ:
    • search - поиск по названию или аббревиатуре
    • ids - фильтр по ID через запятую
    • ordering - сортировка
    • page, limit - пагинация (опционально)
"""
)
class FederalDistrictViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ ФЕДЕРАЛЬНЫМИ ОКРУГАМИ."""
    queryset = FederalDistrict.objects.all().select_related('country').order_by('country__name', 'name')
    serializer_class = FederalDistrictSerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'abbreviated_name']
    ordering_fields = ['name', 'country__name']
    ordering = ['country__name', 'name']
    filterset_fields = ['country']


@extend_schema(
    tags=["Типы регионов"],
    description="""
    Управление типами регионов (область, край, республика и т.д.)

    📌 ПАРАМЕТРЫ:
    • search - поиск по названию или аббревиатуре
    • ids - фильтр по ID через запятую
    • ordering - сортировка
    • page, limit - пагинация (опционально)
    """
)
class TypeRegionViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ ТИПАМИ РЕГИОНОВ."""
    queryset = TypeRegion.objects.all().order_by('name')
    serializer_class = TypeRegionSerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'abbreviated_name']
    ordering_fields = ['name', 'show_before_name', 'skip_in_name']
    ordering = ['name']


@extend_schema(
    tags=["Часовые пояса"],
    description="""
    Управление часовыми поясами для регионов и городов

    📌 ПАРАМЕТРЫ:
    • search - поиск по названию
    • ids - фильтр по ID через запятую
    • ordering - сортировка (по смещению от UTC)
    • page, limit - пагинация (опционально)
    """
)
class TimezoneViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ ЧАСОВЫМИ ПОЯСАМИ."""
    queryset = Timezone.objects.all().order_by('offset_utc')
    serializer_class = TimezoneSerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'offset_utc', 'offset_moscow']
    ordering = ['offset_utc']


@extend_schema(
    tags=["Регионы"],
    description="""
    Управление регионами (субъектами федерации)

    📌 ПАРАМЕТРЫ ФИЛЬТРАЦИИ:
    • search - поиск по названию региона, аббревиатуре или федеральному округу
    • ids - фильтр по ID через запятую
    • federal_districts - фильтр по федеральным округам (uuid1,uuid2)
    • ordering - сортировка
    • page, limit - пагинация (опционально)

    ПРИМЕРЫ:
    • GET /api/addresses/regions/?search=Моск
    • GET /api/addresses/regions/?federal_districts=uuid-цфо
    • GET /api/addresses/regions/?ids=uuid1,uuid2
    """
)
class RegionViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ РЕГИОНАМИ."""
    queryset = Region.objects.all().select_related(
        'federal_district', 'type_region', 'timezone'
    ).order_by('federal_district__name', 'name')

    serializer_class = RegionSerializer
    pagination_class = OptionalPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RegionFilter  # ← С федеральными округами
    ordering = ['federal_district__name', 'name']


@extend_schema(
    tags=["Типы населенных пунктов"],
    description="""
    Управление типами населенных пунктов (город, деревня, поселок и т.д.)

    📌 ПАРАМЕТРЫ:
    • search - поиск по названию или аббревиатуре
    • ids - фильтр по ID через запятую
    • ordering - сортировка
    • page, limit - пагинация (опционально)
    """
)
class LocalityTypeViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ ТИПАМИ НАСЕЛЕННЫХ ПУНКТОВ."""
    queryset = LocalityType.objects.all().order_by('name')
    serializer_class = LocalityTypeSerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'abbreviated_name']
    ordering_fields = ['name', 'has_administrative_territory']
    ordering = ['name']


@extend_schema(
    tags=["Города"],
    description="""
    Управление городами и другими населенными пунктами.

    📌 ПАРАМЕТРЫ ФИЛЬТРАЦИИ:
    • search - поиск по названию города, региона или федерального округа
    • ids - фильтр по ID через запятую
    • regions - фильтр по регионам (uuid1,uuid2)
    • federal_districts - фильтр по федеральным округам (uuid1,uuid2)
    • ordering - сортировка
    • page, limit - пагинация (опционально)

    ПРИМЕРЫ:
    • GET /api/addresses/cities/ → все города
    • GET /api/addresses/cities/?q=Моск → поиск городов
    • GET /api/addresses/cities/?countries=uuid1 → города страны
    • GET /api/addresses/cities/?regions=uuid1,uuid2 → города регионов
    • GET /api/addresses/cities/?page=2&limit=50 → пагинация
    """
)
class CityViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ ГОРОДАМИ."""
    queryset = City.objects.all().select_related(
        'region', 'locality_type', 'timezone'
    ).order_by('region__name', 'name')

    serializer_class = CitySerializer
    pagination_class = OptionalPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = CityFilter  # ← С регионами и федеральными округами
    ordering = ['region__name', 'name']

    @city_list_schema()
    @permission_classes([AllowAny])
    def list(self, request, *args, **kwargs):
        """Список городов."""
        paginator = CustomLimitOffsetPagination()
        # queryset = City.list(request, *args, **kwargs)
        page = paginator.paginate_queryset(self.queryset, request)
        return paginator.get_paginated_response(CitySerializer(page, many=True).data)


@extend_schema(
    tags=["Административные округа"],
    description="""
    Управление административными округами (для крупных городов)

    📌 ПАРАМЕТРЫ:
    • search - поиск по названию
    • ids - фильтр по ID через запятую
    • ordering - сортировка
    • page, limit - пагинация (опционально)
    """
)
class AdministrativeTerritoryViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ АДМИНИСТРАТИВНЫМИ ОКРУГАМИ."""
    queryset = AdministrativeTerritory.objects.all().select_related('city').order_by('city__name', 'name')
    serializer_class = AdministrativeTerritorySerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name']
    ordering_fields = ['name', 'city__name']
    ordering = ['city__name', 'name']
    filterset_fields = ['city']


@extend_schema(
    tags=["Административно-территориальные единицы"],
    description="""
    Управление районами и округами в городах

    📌 ПАРАМЕТРЫ:
    • search - поиск по названию
    • ids - фильтр по ID через запятую
    • ordering - сортировка
    • page, limit - пагинация (опционально)
    """
)
class AdministrativeTerritorialUnitViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ АДМИНИСТРАТИВНО-ТЕРРИТОРИАЛЬНЫМИ ЕДИНИЦАМИ."""
    queryset = AdministrativeTerritorialUnit.objects.all().select_related(
        'city', 'administrative_territory'
    ).order_by('city__name', 'name')

    serializer_class = AdministrativeUnitSerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name']
    ordering_fields = ['name', 'city__name', 'administrative_territory__name']
    ordering = ['city__name', 'name']
    filterset_fields = ['city', 'administrative_territory']


@extend_schema(
    tags=["Типы улиц"],
    description="""
    Управление типами улиц (улица, проспект, переулок и т.д.)

    📌 ПАРАМЕТРЫ:
    • search - поиск по названию или аббревиатуре
    • ids - фильтр по ID через запятую
    • ordering - сортировка
    • page, limit - пагинация (опционально)
    """
)
class StreetTypeViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ ТИПАМИ УЛИЦ."""
    queryset = StreetType.objects.all().order_by('name')
    serializer_class = StreetTypeSerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'abbreviated_name']
    ordering_fields = ['name', 'show_before_name']
    ordering = ['name']


@extend_schema(
    tags=["Улицы"],
    description="""
    Управление улицами, проспектами, переулками и т.д.

    📌 ПАРАМЕТРЫ ФИЛЬТРАЦИИ:
    • search - поиск по названию улицы или города
    • ids - фильтр по ID через запятую
    • cities - фильтр по городам (uuid1,uuid2)
    • ordering - сортировка
    • page, limit - пагинация (опционально)

    ПРИМЕРЫ:
    • GET /api/addresses/streets/ → все улицы
    • GET /api/addresses/streets/?q=Ленина → поиск улиц
    • GET /api/addresses/streets/?cities=uuid1,uuid2 → улицы городов
    • GET /api/addresses/streets/?page=2&limit=50 → пагинация
    """
)
class StreetViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ УЛИЦАМИ."""
    queryset = Street.objects.all().select_related('city', 'street_type').order_by('city__name', 'name')
    serializer_class = StreetSerializer
    pagination_class = OptionalPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = StreetFilter  # ← С городами
    ordering = ['city__name', 'name']

    @street_list_schema()
    def list(self, request, *args, **kwargs):
        """Список улиц."""
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["Дома"],
    description="""
    Управление домами (зданиями) на улицах

    📌 ПАРАМЕТРЫ:
    • search - поиск по номеру дома
    • ids - фильтр по ID через запятую
    • ordering - сортировка
    • page, limit - пагинация (опционально)
    """
)
class HouseViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ ДОМАМИ."""
    queryset = House.objects.all().select_related('street').order_by('street__name', 'number')
    serializer_class = HouseSerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['number']
    ordering_fields = ['number', 'street__name']
    ordering = ['street__name', 'number']
    filterset_fields = ['street']


@extend_schema(
    tags=["Строения"],
    description="""
    Управление строениями и корпусами домов

    📌 ПАРАМЕТРЫ:
    • search - поиск по номеру строения
    • ids - фильтр по ID через запятую
    • ordering - сортировка
    • page, limit - пагинация (опционально)
    """
)
class BuildingViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ СТРОЕНИЯМИ."""
    queryset = Building.objects.all().select_related('house').order_by('house__street__name', 'house__number', 'number')
    serializer_class = BuildingSerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['number']
    ordering_fields = ['number', 'house__number', 'house__street__name']
    ordering = ['house__street__name', 'house__number', 'number']
    filterset_fields = ['house']


@extend_schema(
    tags=["Координаты"],
    description="""
    Управление географическими координатами

    📌 ПАРАМЕТРЫ:
    • search - поиск по широте или долготе
    • ids - фильтр по ID через запятую
    • ordering - сортировка
    • page, limit - пагинация (опционально)
    """
)
class CoordinatesViewSet(viewsets.ModelViewSet):
    serializer_class = CoordinatesSerializers
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['latitude', 'longitude']
    ordering_fields = ['latitude', 'longitude']
    ordering = ['latitude', 'longitude']
    filterset_fields = ['latitude', 'longitude']

# ====================================================================================
# МОДУЛЬ 3: VIEWSET ДЛЯ АДРЕСОВ С ДОПОЛНИТЕЛЬНЫМИ МЕТОДАМИ
# ====================================================================================

@extend_schema(
    tags=["Адреса"],
    description="""
    Управление полными адресами.

    📌 ФИЛЬТРАЦИЯ:
    • search - глобальный поиск по всем компонентам адреса
    • ids - фильтр по ID через запятую
    • ordering - сортировка
    • page, limit - пагинация

    📌 СОЗДАНИЕ АДРЕСОВ:

    1. ПОЛНОЕ СОЗДАНИЕ (со всеми объектами):
       POST /api/addresses/
       {
         "country": {"name": "Россия"},
         "city": {"name": "Москва"},
         "street": {"name": "Ленина"},
         "house": {"number": "1"}
       }

    2. БЫСТРОЕ СОЗДАНИЕ ПО UUID:
       POST /api/addresses/create_by_uuid/
       {
         "country": "uuid-россия",
         "city": "uuid-москва",
         "street": "uuid-ленина", 
         "house": "uuid-дом1"
       }

    📌 ПРИМЕРЫ ЗАПРОСОВ:
    • GET /api/addresses/addresses/?search=Москва Ленина
    • GET /api/addresses/addresses/?ids=uuid1,uuid2,uuid3
    • GET /api/addresses/addresses/?ordering=city__name&page=2
    """
)
class AddressViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ АДРЕСАМИ С УПРОЩЁННОЙ ФИЛЬТРАЦИЕЙ.

    📌 ОСОБЕННОСТИ:
    • Только search и ids фильтры
    • Глобальный поиск по всем полям адреса
    • Пагинация только при ?page=
    • Единый стандарт параметров (page, limit)
    """

    queryset = Address.objects.all().select_related(
        'country', 'federal_district', 'region', 'city',
        'administrative_territory', 'administrative_unit',
        'street', 'house', 'building', 'coordinates'
    ).order_by(
        'country__name', 'region__name', 'city__name',
        'street__name', 'house__number', 'building__number'
    )

    pagination_class = OptionalPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AddressFilter  # ← Упрощённый фильтр
    ordering = ['country__name', 'region__name', 'city__name']

    def get_serializer_class(self):
        """ВЫБОР СЕРИАЛИЗАТОРА."""
        if self.action in ['create', 'update', 'partial_update']:
            return AddressCreateSerializer
        return AddressReadSerializer

    # ==========================================================================
    # СПЕЦИАЛЬНЫЕ МЕТОДЫ (ОСТАВЛЯЕМ ТОЛЬКО НУЖНЫЕ)
    # ==========================================================================

    @extend_schema(
        summary="Создание адреса по UUID",
        description="""
        Быстрое создание адреса по UUID существующих объектов.

        📌 ПРИМЕР ЗАПРОСА:
        ```json
        {
            "country": "550e8400-e29b-41d4-a716-446655440000",
            "city": "550e8400-e29b-41d4-a716-446655440001",
            "street": "550e8400-e29b-41d4-a716-446655440002",
            "house": "550e8400-e29b-41d4-a716-446655440003",
            "index": "101000",
            "coordinates": "550e8400-e29b-41d4-a716-446655440004"
        }
        ```
        """,
        responses={201: AddressReadSerializer}
    )
    @action(detail=False, methods=['post'])
    def create_by_uuid(self, request):
        """Создание адреса по UUID существующих объектов."""
        data = request.data.copy()

        # Валидация иерархии
        errors = self._validate_hierarchy(data)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Подготавливаем данные
        address_data = {}

        try:
            # Получаем объекты по UUID
            from django.shortcuts import get_object_or_404

            if data.get('country'):
                address_data['country'] = get_object_or_404(Country, id=data['country'])

            if data.get('region'):
                address_data['region'] = get_object_or_404(Region, id=data['region'])
                if not address_data.get('country'):
                    address_data['country'] = address_data['region'].federal_district.country

            if data.get('city'):
                address_data['city'] = get_object_or_404(City, id=data['city'])
                if not address_data.get('region'):
                    address_data['region'] = address_data['city'].region

            if data.get('street'):
                address_data['street'] = get_object_or_404(Street, id=data['street'])
                if not address_data.get('city'):
                    address_data['city'] = address_data['street'].city

            if data.get('house'):
                address_data['house'] = get_object_or_404(House, id=data['house'])
                if not address_data.get('street'):
                    address_data['street'] = address_data['house'].street

            if data.get('building'):
                address_data['building'] = get_object_or_404(Building, id=data['building'])
                if not address_data.get('house'):
                    address_data['house'] = address_data['building'].house

            if data.get('coordinates'):
                address_data['coordinates'] = get_object_or_404(Coordinates, id=data['coordinates'])

            # Дополнительные поля
            if data.get('microdistrict'):
                address_data['microdistrict'] = data['microdistrict']
            if data.get('index'):
                address_data['index'] = data['index']

            # Создаем адрес
            serializer = AddressCreateSerializer(data=address_data)
            serializer.is_valid(raise_exception=True)
            address = serializer.save()

            # Возвращаем результат
            read_serializer = AddressReadSerializer(address)
            return Response(
                read_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Статистика по адресам",
        description="""
        Статистическая информация по адресам.
        """
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика по адресам."""
        from django.db.models import Count

        total = Address.objects.count()

        # Базовые статистики
        with_coordinates = Address.objects.filter(
            coordinates__isnull=False
        ).count()

        with_index = Address.objects.filter(
            index__isnull=False
        ).count()

        # Распределение по странам (топ 10)
        by_country = Address.objects.values(
            'country__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Распределение по городам (топ 10)
        by_city = Address.objects.values(
            'city__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Последние созданные адреса
        recent = Address.objects.order_by('-id')[:5].values(
            'id', 'full_address'
        )

        return Response({
            'total': total,
            'with_coordinates': {
                'count': with_coordinates,
                'percentage': round((with_coordinates / total * 100) if total > 0 else 0, 1)
            },
            'with_index': {
                'count': with_index,
                'percentage': round((with_index / total * 100) if total > 0 else 0, 1)
            },
            'by_country': list(by_country),
            'by_city': list(by_city),
            'recent': list(recent)
        })

    # ==========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ==========================================================================

    def _validate_hierarchy(self, data):
        """Валидация иерархии объектов при создании по UUID."""
        errors = {}

        if data.get('house') and not data.get('street'):
            errors['house'] = 'Для дома должна быть указана улица'

        if data.get('building') and not data.get('house'):
            errors['building'] = 'Для строения должен быть указан дом'

        if data.get('street') and not data.get('city'):
            errors['street'] = 'Для улицы должен быть указан город'

        if data.get('city') and not data.get('region'):
            errors['city'] = 'Для города должен быть указан регион'

        return errors if errors else None