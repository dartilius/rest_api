"""
Вьюсеты (ViewSets) для справочника адресов.

МОДУЛЬ VIEWSETS:
─────────────────────────────────────────────────────────────────────────────────────
Этот модуль содержит все ViewSets для работы с моделями адресов через Django REST Framework.
ViewSets обеспечивают CRUD операции для всех моделей адресов, а также специальные методы
для поиска, фильтрации и массовых операций.

СТРУКТУРА VIEWSETS:
─────────────────────────────────────────────────────────────────────────────────────
1. Базовые ViewSets для каждой модели
   • CountryViewSet, FederalDistrictViewSet, RegionViewSet и т.д.
   • Стандартные CRUD операции (list, retrieve, create, update, delete)

2. Специальные ViewSet для адресов
   • AddressViewSet - с дополнительными методами для работы с адресами
   • Поддержка создания с вложенной структурой
   • Поиск и фильтрация адресов

3. Дополнительные методы
   • search - поиск адресов по различным критериям
   • bulk_create - массовое создание адресов
   • create_by_uuid - создание адреса по UUID существующих объектов

ОСОБЕННОСТИ:
• Использование drf-spectacular для автоматической документации
• Гибкая фильтрация и поиск с использованием Django Filter
• Поддержка пагинации
• Валидация иерархии адресов
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import (
    Country, FederalDistrict, TypeRegion, Timezone, Region,
    LocalityType, City, AdministrativeTerritory,
    AdministrativeTerritorialUnit, StreetType, Street,
    House, Building, Address
)
from .serializers import (
    # Базовые сериализаторы
    CountrySerializer, FederalDistrictSerializer, TypeRegionSerializer,
    TimezoneSerializer, RegionSerializer, LocalityTypeSerializer,
    CitySerializer, AdministrativeTerritorySerializer,
    AdministrativeUnitSerializer, StreetTypeSerializer,
    StreetSerializer, HouseSerializer, BuildingSerializer,

    # Сериализаторы для адреса
    AddressReadSerializer, AddressCreateSerializer,
    AddressSearchSerializer, AddressBulkCreateSerializer
)


# ====================================================================================
# МОДУЛЬ 1: КЛАССЫ ПАГИНАЦИИ
# ====================================================================================

class StandardPagination(PageNumberPagination):
    """
    СТАНДАРТНАЯ ПАГИНАЦИЯ для списков объектов.

    НАСТРОЙКИ:
        • page_size: 20 элементов на странице по умолчанию
        • page_size_query_param: возможность изменения размера страницы
        • max_page_size: максимальный размер страницы 100 элементов

    ИСПОЛЬЗУЕТСЯ В:
        • Все ViewSets для списковых представлений
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ====================================================================================
# МОДУЛЬ 2: БАЗОВЫЕ VIEWSETS ДЛЯ ВСЕХ МОДЕЛЕЙ
# ====================================================================================

@extend_schema(
    tags=["Страны"],
    description="Управление странами - корневыми элементами иерархии адресов"
)
class CountryViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ СТРАНАМИ.

    ЭНДПОИНТЫ:
        • GET /api/addresses/countries/ - список стран
        • POST /api/addresses/countries/ - создание страны
        • GET /api/addresses/countries/{id}/ - детали страны
        • PUT /api/addresses/countries/{id}/ - полное обновление страны
        • PATCH /api/addresses/countries/{id}/ - частичное обновление страны
        • DELETE /api/addresses/countries/{id}/ - удаление страны

    ФИЛЬТРАЦИЯ:
        • Поиск по названию (search)
        • Сортировка по названию (ordering)

    ПАГИНАЦИЯ:
        • Стандартная пагинация (20 элементов на странице)
    """

    queryset = Country.objects.all().order_by('name')
    serializer_class = CountrySerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    @extend_schema(
        summary="Поиск стран",
        description="Поиск стран по названию с поддержкой фильтрации и сортировки"
    )
    def list(self, request, *args, **kwargs):
        """Переопределение list для добавления документации."""
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["Федеральные округа"],
    description="Управление федеральными округами (только для России)"
)
class FederalDistrictViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ ФЕДЕРАЛЬНЫМИ ОКРУГАМИ.

    ОГРАНИЧЕНИЯ:
        • Создание только для России
        • Удаление запрещено при наличии связанных регионов

    ФИЛЬТРАЦИЯ:
        • По стране (country)
        • Поиск по названию (search)
        • Сортировка по стране и названию
    """

    queryset = FederalDistrict.objects.all().select_related('country').order_by('country__name', 'name')
    serializer_class = FederalDistrictSerializer
    pagination_class = StandardPagination
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
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ ТИПАМИ РЕГИОНОВ.

    ОСОБЕННОСТИ:
        • Определяет правила отображения регионов
        • Влияет на формирование полного названия региона
    """

    queryset = TypeRegion.objects.all().order_by('name')
    serializer_class = TypeRegionSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'abbreviated_name']
    ordering_fields = ['name', 'show_before_name', 'skip_in_name']
    ordering = ['name']


@extend_schema(
    tags=["Часовые пояса"],
    description="Управление часовыми поясами для регионов и городов"
)
class TimezoneViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ ЧАСОВЫМИ ПОЯСАМИ.

    ОСОБЕННОСТИ:
        • Хранит смещение относительно UTC и Москвы
        • Используется для правильного отображения времени
    """

    queryset = Timezone.objects.all().order_by('offset_utc')
    serializer_class = TimezoneSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'offset_utc', 'offset_moscow']
    ordering = ['offset_utc']


@extend_schema(
    tags=["Регионы"],
    description="Управление регионами (субъектами федерации)"
)
class RegionViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ РЕГИОНАМИ.

    ОСОБЕННОСТИ:
        • Принадлежит федеральному округу (для России)
        • Имеет тип региона
        • Может иметь часовой пояс

    ФИЛЬТРАЦИЯ:
        • По федеральному округу (federal_district)
        • По типу региона (type_region)
        • По часовому поясу (timezone)
        • Поиск по названию
    """

    queryset = Region.objects.all().select_related(
        'federal_district', 'type_region', 'timezone'
    ).order_by('federal_district__name', 'name')

    serializer_class = RegionSerializer
    pagination_class = StandardPagination
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
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ ТИПАМИ НАСЕЛЕННЫХ ПУНКТОВ.

    ОСОБЕННОСТИ:
        • Определяет правила отображения городов
        • Указывает наличие административных округов
    """

    queryset = LocalityType.objects.all().order_by('name')
    serializer_class = LocalityTypeSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'abbreviated_name']
    ordering_fields = ['name', 'has_administrative_territory']
    ordering = ['name']


@extend_schema(
    tags=["Города"],
    description="Управление городами и другими населенными пунктами"
)
class CityViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ ГОРОДАМИ.

    ОСОБЕННОСТИ:
        • Принадлежит региону
        • Имеет тип населенного пункта
        • Может иметь часовой пояс
        • Может иметь административные округа

    ФИЛЬТРАЦИЯ:
        • По региону (region)
        • По типу населенного пункта (locality_type)
        • По часовому поясу (timezone)
        • Поиск по названию
    """

    queryset = City.objects.all().select_related(
        'region', 'locality_type', 'timezone'
    ).order_by('region__name', 'name')

    serializer_class = CitySerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name']
    ordering_fields = ['name', 'region__name', 'locality_type__name']
    ordering = ['region__name', 'name']
    filterset_fields = ['region', 'locality_type', 'timezone', 'has_administrative_territory']


@extend_schema(
    tags=["Административные округа"],
    description="Управление административными округами (для крупных городов)"
)
class AdministrativeTerritoryViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ АДМИНИСТРАТИВНЫМИ ОКРУГАМИ.

    ОГРАНИЧЕНИЯ:
        • Создается только для городов с has_administrative_territory=True

    ФИЛЬТРАЦИЯ:
        • По городу (city)
        • Поиск по названию
    """

    queryset = AdministrativeTerritory.objects.all().select_related('city').order_by('city__name', 'name')
    serializer_class = AdministrativeTerritorySerializer
    pagination_class = StandardPagination
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
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ АДМИНИСТРАТИВНО-ТЕРРИТОРИАЛЬНЫМИ ЕДИНИЦАМИ.

    ОСОБЕННОСТИ:
        • Принадлежит городу
        • Может принадлежать административному округу

    ФИЛЬТРАЦИЯ:
        • По городу (city)
        • По административному округу (administrative_territory)
        • Поиск по названию
    """

    queryset = AdministrativeTerritorialUnit.objects.all().select_related(
        'city', 'administrative_territory'
    ).order_by('city__name', 'name')

    serializer_class = AdministrativeUnitSerializer
    pagination_class = StandardPagination
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
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ ТИПАМИ УЛИЦ.

    ОСОБЕННОСТИ:
        • Определяет правила отображения улиц
        • Влияет на формирование полного названия улицы
    """

    queryset = StreetType.objects.all().order_by('name')
    serializer_class = StreetTypeSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'abbreviated_name']
    ordering_fields = ['name', 'show_before_name']
    ordering = ['name']


@extend_schema(
    tags=["Улицы"],
    description="Управление улицами, проспектами, переулками и т.д."
)
class StreetViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ УЛИЦАМИ.

    ОСОБЕННОСТИ:
        • Принадлежит городу
        • Может иметь тип улицы

    ФИЛЬТРАЦИЯ:
        • По городу (city)
        • По типу улицы (street_type)
        • Поиск по названию
    """

    queryset = Street.objects.all().select_related('city', 'street_type').order_by('city__name', 'name')
    serializer_class = StreetSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name']
    ordering_fields = ['name', 'city__name', 'street_type__name']
    ordering = ['city__name', 'name']
    filterset_fields = ['city', 'street_type']


@extend_schema(
    tags=["Дома"],
    description="Управление домами (зданиями) на улицах"
)
class HouseViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ ДОМАМИ.

    ОСОБЕННОСТИ:
        • Принадлежит улице
        • Имеет номер дома

    ФИЛЬТРАЦИЯ:
        • По улице (street)
        • Поиск по номеру дома
    """

    queryset = House.objects.all().select_related('street').order_by('street__name', 'number')
    serializer_class = HouseSerializer
    pagination_class = StandardPagination
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
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ СТРОЕНИЯМИ.

    ОСОБЕННОСТИ:
        • Принадлежит дому
        • Имеет номер строения/корпуса

    ФИЛЬТРАЦИЯ:
        • По дому (house)
        • Поиск по номеру строения
    """

    queryset = Building.objects.all().select_related('house').order_by('house__street__name', 'house__number', 'number')
    serializer_class = BuildingSerializer
    pagination_class = StandardPagination
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
    description="Управление полными адресами со всей иерархией"
)
class AddressViewSet(viewsets.ModelViewSet):
    """
    VIEWSET ДЛЯ УПРАВЛЕНИЯ АДРЕСАМИ.

    ОПИСАНИЕ:
        Основной ViewSet для работы с полными адресами. Поддерживает создание
        адресов с глубоко вложенной структурой, поиск, фильтрацию и массовые операции.

    ЭНДПОИНТЫ:
        • GET /api/addresses/addresses/ - список адресов
        • POST /api/addresses/addresses/ - создание адреса
        • GET /api/addresses/addresses/{id}/ - детали адреса
        • PUT /api/addresses/addresses/{id}/ - обновление адреса
        • DELETE /api/addresses/addresses/{id}/ - удаление адреса

    СПЕЦИАЛЬНЫЕ ЭНДПОИНТЫ:
        • POST /api/addresses/addresses/search/ - поиск адресов
        • POST /api/addresses/addresses/bulk_create/ - массовое создание
        • POST /api/addresses/addresses/create_by_uuid/ - создание по UUID

    ОСОБЕННОСТИ:
        • Автоматический выбор сериализатора (чтение/создание)
        • Проверка целостности иерархии
        • Автоматическое заполнение недостающих полей
        • Поиск существующих адресов перед созданием
    """

    queryset = Address.objects.all().select_related(
        'country', 'federal_district', 'region', 'city',
        'administrative_territory', 'administrative_unit',
        'street', 'house', 'building'
    ).order_by(
        'country__name', 'region__name', 'city__name',
        'street__name', 'house__number', 'building__number'
    )

    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = [
        'country__name',
        'region__name',
        'city__name',
        'street__name',
        'house__number',
        'building__number',
        'microdistrict',
        'index'
    ]
    ordering_fields = [
        'country__name', 'region__name', 'city__name',
        'street__name', 'house__number', 'building__number',
        'index', 'microdistrict'
    ]
    ordering = ['country__name', 'region__name', 'city__name']
    filterset_fields = [
        'country', 'federal_district', 'region', 'city',
        'administrative_territory', 'administrative_unit',
        'street', 'house', 'building'
    ]

    def get_serializer_class(self):
        """
        ВЫБОР СЕРИАЛИЗАТОРА В ЗАВИСИМОСТИ ОТ ДЕЙСТВИЯ.

        ЛОГИКА:
            • Для создания и обновления: AddressCreateSerializer
            • Для всех остальных действий: AddressReadSerializer

        ВОЗВРАЩАЕТ:
            Serializer class : Класс сериализатора

        ИСПОЛЬЗУЕТСЯ В:
            • create, update, partial_update - AddressCreateSerializer
            • list, retrieve, destroy - AddressReadSerializer
        """
        if self.action in ['create', 'update', 'partial_update']:
            return AddressCreateSerializer
        return AddressReadSerializer

    # ==========================================================================
    # ОСНОВНЫЕ МЕТОДЫ CRUD
    # ==========================================================================

    @extend_schema(
        summary="Список адресов",
        description="Получение списка адресов с поддержкой поиска, фильтрации и сортировки"
    )
    def list(self, request, *args, **kwargs):
        """Переопределение list для добавления документации."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Детали адреса",
        description="Получение полной информации об адресе со всеми компонентами"
    )
    def retrieve(self, request, *args, **kwargs):
        """Переопределение retrieve для добавления документации."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Создание адреса",
        description="Создание адреса с возможностью указания вложенной структуры"
    )
    def create(self, request, *args, **kwargs):
        """
        СОЗДАНИЕ НОВОГО АДРЕСА.

        ОСОБЕННОСТИ:
            • Обработка вложенной структуры
            • Автоматическое создание связанных объектов
            • Проверка существования такого же адреса

        ПАРАМЕТРЫ ЗАПРОСА:
            • Может принимать как плоскую структуру, так и вложенную под ключ 'address'

        ВОЗВРАЩАЕТ:
            • 201 Created: При успешном создании
            • 400 Bad Request: При ошибках валидации

        ПРИМЕР ЗАПРОСА:
            {
                "country": {"name": "Россия"},
                "region": {"name": "Московская"},
                "city": {"name": "Москва"},
                "street": {"name": "Ленина"},
                "house": {"number": "1"},
                "index": "101000"
            }
        """
        # Обрабатываем вложенную структуру
        if 'address' in request.data:
            address_data = request.data['address']
        else:
            address_data = request.data

        serializer = self.get_serializer(data=address_data)
        serializer.is_valid(raise_exception=True)

        # Создаем адрес
        address = serializer.save()

        # Всегда возвращаем полную расшифровку адреса
        read_serializer = AddressReadSerializer(address)
        headers = self.get_success_headers(read_serializer.data)

        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @extend_schema(
        summary="Обновление адреса",
        description="Полное обновление адреса"
    )
    def update(self, request, *args, **kwargs):
        """Переопределение update для работы с вложенной структурой."""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частичное обновление адреса",
        description="Частичное обновление адреса"
    )
    def partial_update(self, request, *args, **kwargs):
        """Переопределение partial_update для работы с вложенной структурой."""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удаление адреса",
        description="Удаление адреса по идентификатору"
    )
    def destroy(self, request, *args, **kwargs):
        """Переопределение destroy для добавления документации."""
        return super().destroy(request, *args, **kwargs)

    # ==========================================================================
    # СПЕЦИАЛЬНЫЕ МЕТОДЫ И ЭКШЕНЫ
    # ==========================================================================

    @extend_schema(
        summary="Создание адреса по UUID",
        description="Создание адреса по UUID существующих объектов иерархии",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'country': {'type': 'string', 'format': 'uuid'},
                    'region': {'type': 'string', 'format': 'uuid'},
                    'city': {'type': 'string', 'format': 'uuid'},
                    'street': {'type': 'string', 'format': 'uuid'},
                    'house': {'type': 'string', 'format': 'uuid'},
                    'building': {'type': 'string', 'format': 'uuid'},
                    'microdistrict': {'type': 'string'},
                    'index': {'type': 'string', 'maxLength': 6},
                    'coordinates': {'type': 'string'}
                }
            }
        },
        responses={201: AddressReadSerializer}
    )
    @action(detail=False, methods=['post'])
    def create_by_uuid(self, request):
        """
        СОЗДАНИЕ АДРЕСА ПО UUID СУЩЕСТВУЮЩИХ ОБЪЕКТОВ.

        ОПИСАНИЕ:
            Альтернативный способ создания адреса, когда все компоненты
            уже существуют в системе и известны их UUID.

        ПРЕИМУЩЕСТВА:
            • Быстрее, чем создание с вложенной структурой
            • Не требует передачи полных данных объектов
            • Идеально для интеграции с другими системами

        ПАРАМЕТРЫ ЗАПРОСА:
            • country, region, city, street, house, building: UUID объектов
            • microdistrict, index, coordinates: дополнительные поля

        ВОЗВРАЩАЕТ:
            • 201 Created: При успешном создании
            • 400 Bad Request: При ошибках валидации или отсутствии объектов
            • 404 Not Found: Если объект по UUID не найден

        ПРИМЕР ЗАПРОСА:
            {
                "country": "550e8400-e29b-41d4-a716-446655440000",
                "region": "550e8400-e29b-41d4-a716-446655440001",
                "city": "550e8400-e29b-41d4-a716-446655440002",
                "street": "550e8400-e29b-41d4-a716-446655440003",
                "house": "550e8400-e29b-41d4-a716-446655440004",
                "building": "550e8400-e29b-41d4-a716-446655440005",
                "index": "101000"
            }
        """
        data = request.data.copy()

        # Проверяем иерархию
        errors = self._validate_hierarchy(data)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Подготавливаем данные для создания адреса
        address_data = {}

        # Получаем связанные объекты по UUID
        try:
            address_data.update(self._get_objects_by_uuid(data))
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Добавляем дополнительные поля
        if data.get('microdistrict'):
            address_data['microdistrict'] = data['microdistrict']
        if data.get('index'):
            address_data['index'] = data['index']
        if data.get('coordinates'):
            address_data['coordinates'] = data['coordinates']

        # Создаем адрес
        serializer = AddressCreateSerializer(data=address_data)
        serializer.is_valid(raise_exception=True)
        address = serializer.save()

        # Возвращаем полный адрес
        read_serializer = AddressReadSerializer(address)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Поиск адресов",
        description="Расширенный поиск адресов по различным критериям",
        request=AddressSearchSerializer,
        responses={200: AddressReadSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def search(self, request):
        """
        РАСШИРЕННЫЙ ПОИСК АДРЕСОВ.

        ОПИСАНИЕ:
            Поиск адресов по различным критериям с поддержкой пагинации.
            Поддерживает как точные фильтры по UUID, так и текстовый поиск.

        ПАРАМЕТРЫ ПОИСКА:
            • query: общий текстовый поиск
            • country, region, city, street: фильтры по UUID
            • index: фильтр по почтовому индексу
            • limit, offset: пагинация

        ВОЗВРАЩАЕТ:
            • 200 OK: Список найденных адресов
            • 400 Bad Request: При ошибках валидации параметров

        ПРИМЕР ЗАПРОСА:
            {
                "query": "Москва Ленина",
                "country": "550e8400-e29b-41d4-a716-446655440000",
                "limit": 10,
                "offset": 0
            }
        """
        # Валидируем параметры поиска
        search_serializer = AddressSearchSerializer(data=request.data)
        search_serializer.is_valid(raise_exception=True)

        validated_data = search_serializer.validated_data

        # Начинаем с базового queryset
        queryset = self.get_queryset()

        # Применяем фильтры по UUID
        if validated_data.get('country'):
            queryset = queryset.filter(country_id=validated_data['country'])

        if validated_data.get('region'):
            queryset = queryset.filter(region_id=validated_data['region'])

        if validated_data.get('city'):
            queryset = queryset.filter(city_id=validated_data['city'])

        if validated_data.get('street'):
            queryset = queryset.filter(street_id=validated_data['street'])

        # Применяем фильтр по индексу
        if validated_data.get('index'):
            queryset = queryset.filter(index=validated_data['index'])

        # Применяем текстовый поиск
        if validated_data.get('query'):
            query = validated_data['query']
            # Используем сложный поиск по нескольким полям
            from django.db.models import Q

            queryset = queryset.filter(
                Q(country__name__icontains=query) |
                Q(region__name__icontains=query) |
                Q(city__name__icontains=query) |
                Q(street__name__icontains=query) |
                Q(house__number__icontains=query) |
                Q(building__number__icontains=query) |
                Q(microdistrict__icontains=query) |
                Q(index__icontains=query)
            )

        # Применяем пагинацию
        limit = validated_data.get('limit', 20)
        offset = validated_data.get('offset', 0)

        total_count = queryset.count()
        queryset = queryset[offset:offset + limit]

        # Сериализуем результаты
        serializer = AddressReadSerializer(queryset, many=True)

        return Response({
            'count': total_count,
            'next': None if offset + limit >= total_count else offset + limit,
            'previous': None if offset == 0 else max(0, offset - limit),
            'results': serializer.data
        })

    @extend_schema(
        summary="Массовое создание адресов",
        description="Создание нескольких адресов за один запрос",
        request=AddressBulkCreateSerializer,
        responses={201: AddressReadSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        МАССОВОЕ СОЗДАНИЕ АДРЕСОВ.

        ОПИСАНИЕ:
            Создание нескольких адресов за один запрос. Полезно для
            импорта данных или пакетной обработки.

        ПАРАМЕТРЫ ЗАПРОСА:
            • addresses: список объектов адресов для создания

        ВОЗВРАЩАЕТ:
            • 201 Created: Список созданных адресов
            • 400 Bad Request: При ошибках валидации

        ПРИМЕР ЗАПРОСА:
            {
                "addresses": [
                    {
                        "country": {"name": "Россия"},
                        "city": {"name": "Москва"},
                        "street": {"name": "Ленина"},
                        "house": {"number": "1"}
                    },
                    {
                        "country": {"name": "Россия"},
                        "city": {"name": "Санкт-Петербург"},
                        "street": {"name": "Невский проспект"},
                        "house": {"number": "10"}
                    }
                ]
            }
        """
        serializer = AddressBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        # Сериализуем созданные адреса для ответа
        addresses = result['addresses']
        read_serializer = AddressReadSerializer(addresses, many=True)

        return Response(
            {'addresses': read_serializer.data},
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Статистика по адресам",
        description="Получение статистической информации по адресам",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'total_addresses': {'type': 'integer'},
                    'by_country': {'type': 'object'},
                    'by_region': {'type': 'object'},
                    'by_city': {'type': 'object'}
                }
            }
        }
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        ПОЛУЧЕНИЕ СТАТИСТИКИ ПО АДРЕСАМ.

        ВОЗВРАЩАЕТ:
            • Общее количество адресов
            • Распределение по странам
            • Распределение по регионам
            • Распределение по городам
        """
        from django.db.models import Count

        # Общее количество адресов
        total_addresses = Address.objects.count()

        # Распределение по странам
        by_country = Address.objects.values(
            'country__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

        # Распределение по регионам
        by_region = Address.objects.values(
            'region__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

        # Распределение по городам
        by_city = Address.objects.values(
            'city__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'total_addresses': total_addresses,
            'by_country': list(by_country),
            'by_region': list(by_region),
            'by_city': list(by_city)
        })

    # ==========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ==========================================================================

    def _validate_hierarchy(self, data):
        """
        ПРОВЕРКА ИЕРАРХИИ ОБЪЕКТОВ ПРИ СОЗДАНИИ ПО UUID.

        ВЫПОЛНЯЕМЫЕ ПРОВЕРКИ:
            1. Если указан дом, должна быть указана улица
            2. Если указано строение, должен быть указан дом
            3. Если указана улица, должен быть указан город
            4. Если указан город, должен быть указан регион

        АРГУМЕНТЫ:
            data : dict
                Данные запроса

        ВОЗВРАЩАЕТ:
            dict or None: Ошибки валидации или None
        """
        errors = {}

        # Проверка 1: Дом требует улицу
        if data.get('house') and not data.get('street'):
            errors['house'] = 'Для дома должна быть указана улица'

        # Проверка 2: Строение требует дом
        if data.get('building') and not data.get('house'):
            errors['building'] = 'Для строения должен быть указан дом'

        # Проверка 3: Улица требует город
        if data.get('street') and not data.get('city'):
            errors['street'] = 'Для улицы должен быть указан город'

        # Проверка 4: Город требует регион
        if data.get('city') and not data.get('region'):
            errors['city'] = 'Для города должен быть указан регион'

        # Проверка 5: Регион требует страну (опционально, может быть выведена)
        if data.get('region') and not data.get('country'):
            # Предупреждение, но не ошибка
            pass

        return errors if errors else None

    def _get_objects_by_uuid(self, data):
        """
        ПОЛУЧЕНИЕ ОБЪЕКТОВ ПО UUID ИЗ ЗАПРОСА.

        АРГУМЕНТЫ:
            data : dict
                Данные запроса с UUID объектов

        ВОЗВРАЩАЕТ:
            dict : Словарь с объектами для создания адреса

        ИСКЛЮЧЕНИЯ:
            Exception: Если объект не найден
        """
        from django.shortcuts import get_object_or_404

        address_data = {}

        # Получаем объекты по UUID
        if data.get('country'):
            address_data['country'] = get_object_or_404(Country, id=data['country'])

        if data.get('region'):
            address_data['region'] = get_object_or_404(Region, id=data['region'])

            # Автоматически заполняем страну и федеральный округ из региона
            if not address_data.get('country'):
                address_data['country'] = address_data['region'].federal_district.country

            if not data.get('federal_district'):
                address_data['federal_district'] = address_data['region'].federal_district

        if data.get('city'):
            address_data['city'] = get_object_or_404(City, id=data['city'])

            # Автоматически заполняем регион из города
            if not address_data.get('region'):
                address_data['region'] = address_data['city'].region

        if data.get('street'):
            address_data['street'] = get_object_or_404(Street, id=data['street'])

            # Автоматически заполняем город из улицы
            if not address_data.get('city'):
                address_data['city'] = address_data['street'].city

        if data.get('house'):
            address_data['house'] = get_object_or_404(House, id=data['house'])

            # Автоматически заполняем улицу из дома
            if not address_data.get('street'):
                address_data['street'] = address_data['house'].street

        if data.get('building'):
            address_data['building'] = get_object_or_404(Building, id=data['building'])

            # Автоматически заполняем дом из строения
            if not address_data.get('house'):
                address_data['house'] = address_data['building'].house

        # Автоматически заполняем недостающие поля из иерархии
        if address_data.get('city') and not address_data.get('region'):
            address_data['region'] = address_data['city'].region

        if address_data.get('region') and not address_data.get('country'):
            address_data['country'] = address_data['region'].federal_district.country

        if address_data.get('region') and not address_data.get('federal_district'):
            address_data['federal_district'] = address_data['region'].federal_district

        return address_data
