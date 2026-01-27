"""
Вьюсеты (ViewSets) для справочника адресов с отключенной пагинацией.

МОДУЛЬ VIEWSETS:
─────────────────────────────────────────────────────────────────────────────────────
Все ViewSets возвращают полные наборы данных без пагинации по умолчанию.
Пагинация доступна только при явном указании параметра ?page=

СТРУКТУРА ОТВЕТА БЕЗ ПАГИНАЦИИ:
{
    "count": 1250,
    "results": [... все записи ...]
}

СТРУКТУРА ОТВЕТА С ПАГИНАЦИЕЙ (?page=2):
{
    "count": 1250,
    "next": "http://api/addresses/?page=3",
    "previous": "http://api/addresses/?page=1",
    "results": [... записи страницы 2 ...]
}

ОСОБЕННОСТИ:
• Пагинация отключена глобально в settings.py (DEFAULT_PAGINATION_CLASS: None)
• Параметр ?page= включает пагинацию с размером страницы 100
• Параметр ?page_size= меняет размер страницы при использовании ?page=
• Все остальные параметры работают одинаково с пагинацией и без неё
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema

from .models import (
    Country, FederalDistrict, TypeRegion, Timezone, Region,
    LocalityType, City, AdministrativeTerritory,
    AdministrativeTerritorialUnit, StreetType, Street,
    House, Building, Address
)
from .serializers import (
    CountrySerializer, FederalDistrictSerializer, TypeRegionSerializer,
    TimezoneSerializer, RegionSerializer, LocalityTypeSerializer,
    CitySerializer, AdministrativeTerritorySerializer,
    AdministrativeUnitSerializer, StreetTypeSerializer,
    StreetSerializer, HouseSerializer, BuildingSerializer,
    AddressReadSerializer, AddressCreateSerializer,
    AddressSearchSerializer, AddressBulkCreateSerializer
)
from .filters import (
    CountryFilter, CityFilter, StreetFilter, AddressFilter
)
from .schemas import (
    address_list_schema, country_list_schema,
    city_list_schema, street_list_schema
)


# ====================================================================================
# МОДУЛЬ 1: КЛАСС ПАГИНАЦИИ, КОТОРЫЙ РАБОТАЕТ ТОЛЬКО С ПАРАМЕТРОМ ?page=
# ====================================================================================

class OptionalPagination(PageNumberPagination):
    """
    ПАГИНАЦИЯ, КОТОРАЯ ВКЛЮЧАЕТСЯ ТОЛЬКО ПРИ УКАЗАНИИ ПАРАМЕТРА ?page=

    ПОВЕДЕНИЕ:
    1. Без параметров → возвращаются ВСЕ данные
    2. С параметром ?page= → включается пагинация
    3. С параметрами ?page= и ?page_size= → пагинация с указанным размером

    ПРИМЕРЫ:
    • GET /api/addresses/addresses/ → все адреса
    • GET /api/addresses/addresses/?page=2 → пагинация (страница 2, размер 100)
    • GET /api/addresses/addresses/?page=1&page_size=50 → страница 1, 50 записей
    • GET /api/addresses/addresses/?search=Москва → все адреса Москвы

    ОГРАНИЧЕНИЯ:
    • Максимальный размер страницы: 1000 записей
    • Минимальный размер страницы: 1 запись
    """

    page_size = 100  # Размер страницы по умолчанию при включении пагинации
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        """
        ВКЛЮЧАЕМ ПАГИНАЦИЮ ТОЛЬКО ЕСЛИ УКАЗАН ПАРАМЕТР ?page=

        ЛОГИКА:
        1. Если есть параметр ?page= → включаем пагинацию
        2. Если нет параметра ?page= → возвращаем None (все данные)
        3. Размер страницы берется из ?page_size= или используем page_size
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
            "next": "http://.../?page=3",
            "previous": "http://.../?page=1",
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
        1. Если указан ?page_size= → используем его
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
    
    📌 ПАГИНАЦИЯ: Отключена по умолчанию.
    Для включения пагинации используйте параметр ?page=
    
    ПРИМЕРЫ:
    • GET /api/addresses/countries/ → все страны
    • GET /api/addresses/countries/?q=Рос → поиск стран с "Рос"
    • GET /api/addresses/countries/?page=2 → страница 2 (пагинация)
    • GET /api/addresses/countries/?ids=uuid1,uuid2 → фильтр по ID
    """
)
class CountryViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ СТРАНАМИ.

    ПАГИНАЦИЯ: Включена только при ?page=
    """
    queryset = Country.objects.all().order_by('name')
    serializer_class = CountrySerializer
    pagination_class = OptionalPagination  # Пагинация только с ?page=
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = CountryFilter
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    @country_list_schema()
    def list(self, request, *args, **kwargs):
        """Список стран."""
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["Федеральные округа"],
    description="Управление федеральными округами (только для России)"
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
    description="Управление типами регионов (область, край, республика и т.д.)"
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
    description="Управление часовыми поясами для регионов и городов"
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
    description="Управление регионами (субъектами федерации)"
)
class RegionViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ РЕГИОНАМИ."""
    queryset = Region.objects.all().select_related(
        'federal_district', 'type_region', 'timezone'
    ).order_by('federal_district__name', 'name')

    serializer_class = RegionSerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'abbreviated_name']
    ordering_fields = ['name', 'federal_district__name', 'type_region__name']
    ordering = ['federal_district__name', 'name']
    filterset_fields = ['federal_district', 'type_region', 'timezone']


@extend_schema(
    tags=["Типы населенных пунктов"],
    description="Управление типами населенных пунктов (город, деревня, поселок и т.д.)"
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
    
    ПРИМЕРЫ:
    • GET /api/addresses/cities/ → все города
    • GET /api/addresses/cities/?q=Моск → поиск городов
    • GET /api/addresses/cities/?countries=uuid1 → города страны
    • GET /api/addresses/cities/?regions=uuid1,uuid2 → города регионов
    • GET /api/addresses/cities/?page=2 → пагинация
    """
)
class CityViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ ГОРОДАМИ."""
    queryset = City.objects.all().select_related(
        'region', 'locality_type', 'timezone'
    ).order_by('region__name', 'name')

    serializer_class = CitySerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = CityFilter
    search_fields = ['name']
    ordering_fields = ['name', 'region__name', 'locality_type__name']
    ordering = ['region__name', 'name']

    @city_list_schema()
    def list(self, request, *args, **kwargs):
        """Список городов."""
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["Административные округа"],
    description="Управление административными округами (для крупных городов)"
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
    description="Управление районами и округами в городах"
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
    description="Управление типами улиц (улица, проспект, переулок и т.д.)"
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
    
    ПРИМЕРЫ:
    • GET /api/addresses/streets/ → все улицы
    • GET /api/addresses/streets/?q=Ленина → поиск улиц
    • GET /api/addresses/streets/?cities=uuid1,uuid2 → улицы городов
    • GET /api/addresses/streets/?page=2&page_size=50 → пагинация
    """
)
class StreetViewSet(viewsets.ModelViewSet):
    """VIEWSET ДЛЯ УПРАВЛЕНИЯ УЛИЦАМИ."""
    queryset = Street.objects.all().select_related('city', 'street_type').order_by('city__name', 'name')
    serializer_class = StreetSerializer
    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = StreetFilter
    search_fields = ['name']
    ordering_fields = ['name', 'city__name', 'street_type__name']
    ordering = ['city__name', 'name']

    @street_list_schema()
    def list(self, request, *args, **kwargs):
        """Список улиц."""
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["Дома"],
    description="Управление домами (зданиями) на улицах"
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
    description="Управление строениями и корпусами домов"
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


# ====================================================================================
# МОДУЛЬ 3: VIEWSET ДЛЯ АДРЕСОВ С ДОПОЛНИТЕЛЬНЫМИ МЕТОДАМИ
# ====================================================================================

@extend_schema(
    tags=["Адреса"],
    description="""
    Управление полными адресами со всей иерархией.
    
    📌 ПАГИНАЦИЯ: Отключена по умолчанию.
    
    🔍 ПРИМЕРЫ ЗАПРОСОВ:
    
    1. ВСЕ АДРЕСА (без пагинации):
       GET /api/addresses/addresses/
    
    2. УНИВЕРСАЛЬНЫЙ ПОИСК:
       GET /api/addresses/addresses/?q=Москва Ленина 1
    
    3. ФИЛЬТРАЦИЯ ПО СТРАНАМ И ГОРОДАМ:
       GET /api/addresses/addresses/?countries=uuid1,uuid2&cities=uuid3,uuid4
    
    4. ТОЛЬКО С КООРДИНАТАМИ:
       GET /api/addresses/addresses/?has_coordinates=true
    
    5. ГЕОПОИСК (в радиусе 5 км):
       GET /api/addresses/addresses/?near=55.7558,37.6173,5
    
    6. ПАГИНАЦИЯ (если нужно):
       GET /api/addresses/addresses/?page=2&page_size=50
       GET /api/addresses/addresses/?page=1&page_size=100&q=Москва
    
    7. СОРТИРОВКА:
       GET /api/addresses/addresses/?ordering=city__name,-street__name
    
    📦 ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ:
    
    • POST /api/addresses/addresses/search/      - расширенный поиск
    • POST /api/addresses/addresses/bulk_create/ - массовое создание
    • POST /api/addresses/addresses/create_by_uuid/ - создание по UUID
    • GET  /api/addresses/addresses/statistics/  - статистика
    """
)
class AddressViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ АДРЕСАМИ.

    ОСОБЕННОСТИ:
    • Пагинация отключена по умолчанию (включается только с ?page=)
    • Упрощенные фильтры для фронтенда
    • Поддержка массовых операций
    • Автоматическая проверка дубликатов
    """

    queryset = Address.objects.all().select_related(
        'country', 'federal_district', 'region', 'city',
        'administrative_territory', 'administrative_unit',
        'street', 'house', 'building'
    ).order_by(
        'country__name', 'region__name', 'city__name',
        'street__name', 'house__number', 'building__number'
    )

    pagination_class = OptionalPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = AddressFilter
    ordering_fields = [
        'country__name', 'region__name', 'city__name',
        'street__name', 'house__number', 'building__number',
        'index', 'microdistrict', 'latitude', 'longitude'
    ]
    ordering = ['country__name', 'region__name', 'city__name']

    def get_serializer_class(self):
        """ВЫБОР СЕРИАЛИЗАТОРА В ЗАВИСИМОСТИ ОТ ДЕЙСТВИЯ."""
        if self.action in ['create', 'update', 'partial_update']:
            return AddressCreateSerializer
        return AddressReadSerializer

    @address_list_schema()
    def list(self, request, *args, **kwargs):
        """
        СПИСОК АДРЕСОВ.

        ВОЗВРАЩАЕТ ВСЕ АДРЕСА БЕЗ ПАГИНАЦИИ ПО УМОЛЧАНИЮ.
        ДЛЯ ВКЛЮЧЕНИЯ ПАГИНАЦИИ ИСПОЛЬЗУЙТЕ ПАРАМЕТР ?page=
        """
        return super().list(request, *args, **kwargs)

    # ==========================================================================
    # СПЕЦИАЛЬНЫЕ МЕТОДЫ
    # ==========================================================================

    @extend_schema(
        summary="Расширенный поиск адресов",
        description="""
        Расширенный поиск адресов с поддержкой всех фильтров.
        Используйте этот метод для сложных запросов.
        
        ПРИМЕР ЗАПРОСА:
        ```json
        {
            "q": "Москва Ленина",
            "countries": ["uuid1", "uuid2"],
            "has_coordinates": true,
            "ordering": ["city__name", "-street__name"],
            "limit": 100,
            "offset": 0
        }
        ```
        """,
        request=AddressSearchSerializer,
        responses={200: AddressReadSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Расширенный поиск адресов."""
        search_serializer = AddressSearchSerializer(data=request.data)
        search_serializer.is_valid(raise_exception=True)

        validated_data = search_serializer.validated_data
        queryset = self.get_queryset()

        # Применяем фильтры
        if validated_data.get('query'):
            # Используем наш фильтр для поиска
            address_filter = AddressFilter(
                {'q': validated_data['query']},
                queryset=queryset,
                request=request
            )
            queryset = address_filter.qs

        # Применяем другие фильтры
        if validated_data.get('country'):
            queryset = queryset.filter(country_id=validated_data['country'])

        if validated_data.get('city'):
            queryset = queryset.filter(city_id=validated_data['city'])

        if validated_data.get('limit'):
            limit = validated_data['limit']
            offset = validated_data.get('offset', 0)
            queryset = queryset[offset:offset + limit]

        serializer = AddressReadSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Массовое создание адресов",
        description="""
        Создание нескольких адресов за один запрос.
        Идеально для импорта данных.
        
        ПРИМЕР ЗАПРОСА:
        ```json
        {
            "addresses": [
                {
                    "country": {"name": "Россия"},
                    "city": {"name": "Москва"},
                    "street": {"name": "Ленина"},
                    "house": {"number": "1"},
                    "index": "101000"
                },
                {
                    "country": {"name": "Россия"},
                    "city": {"name": "Санкт-Петербург"},
                    "street": {"name": "Невский проспект"},
                    "house": {"number": "10"}
                }
            ]
        }
        ```
        """,
        request=AddressBulkCreateSerializer,
        responses={201: AddressReadSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Массовое создание адресов."""
        serializer = AddressBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()
        addresses = result['addresses']
        read_serializer = AddressReadSerializer(addresses, many=True)

        return Response(
            {'addresses': read_serializer.data},
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Создание адреса по UUID",
        description="""
        Создание адреса по UUID существующих объектов.
        Быстрее, чем создание с полной структурой.
        
        ПРИМЕР ЗАПРОСА:
        ```json
        {
            "country": "550e8400-e29b-41d4-a716-446655440000",
            "city": "550e8400-e29b-41d4-a716-446655440001",
            "street": "550e8400-e29b-41d4-a716-446655440002",
            "house": "550e8400-e29b-41d4-a716-446655440003",
            "index": "101000",
            "latitude": "55.7558",
            "longitude": "37.6173"
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

            # Дополнительные поля
            if data.get('microdistrict'):
                address_data['microdistrict'] = data['microdistrict']
            if data.get('index'):
                address_data['index'] = data['index']
            if data.get('latitude'):
                address_data['latitude'] = data['latitude']
            if data.get('longitude'):
                address_data['longitude'] = data['longitude']

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
        Получение статистической информации по адресам.
        
        ВОЗВРАЩАЕТ:
        • Общее количество адресов
        • Распределение по странам
        • Распределение по регионам
        • Распределение по городам
        • Процент адресов с координатами
        • Процент адресов с почтовым индексом
        """
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика по адресам."""
        from django.db.models import Count, Q, F, ExpressionWrapper, FloatField
        from django.db.models.functions import Cast

        total = Address.objects.count()

        # Базовые статистики
        with_coordinates = Address.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
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