"""
Фильтры для справочника адресов с поддержкой удобного API для фронтенда.

МОДУЛЬ ФИЛЬТРОВ:
─────────────────────────────────────────────────────────────────────────────────────
Упрощенные фильтры для фронтенда с поддержкой:
• Универсального поиска по всем полям
• Мультивыбора по ID через запятую
• Географического поиска
• Булевых фильтров
• Сортировки по любым полям

ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:
─────────────────────────────────────────────────────────────────────────────────────
1. Поиск адресов в Москве на улице Ленина:
   GET /api/addresses/addresses/?q=Москва Ленина

2. Фильтрация по нескольким странам и городам:
   GET /api/addresses/addresses/?countries=uuid1,uuid2&cities=uuid3,uuid4

3. Поиск в радиусе 5 км от точки:
   GET /api/addresses/addresses/?near=55.7558,37.6173,5

4. Только адреса с координатами и почтовым индексом:
   GET /api/addresses/addresses/?has_coordinates=true&has_index=true

5. Сортировка по городу и улице:
   GET /api/addresses/addresses/?ordering=city__name,street__name
"""

import uuid
from django.db import models
from django.db.models import Q, F, Value
from django.db.models.functions import Concat
from django.db.models.fields import CharField
from django_filters import (
    FilterSet, CharFilter, UUIDFilter, BaseInFilter,
    OrderingFilter, NumberFilter, ChoiceFilter, BooleanFilter
)
from .models import (
    Country, Region, City, Street, House, Building, Address,
    FederalDistrict, TypeRegion, LocalityType, StreetType
)


# ====================================================================================
# МОДУЛЬ 1: КАСТОМНЫЕ ФИЛЬТРЫ ДЛЯ УДОБНОГО API
# ====================================================================================

class UUIDCommaInFilter(BaseInFilter, UUIDFilter):
    """
    ФИЛЬТРАЦИЯ ПО СПИСКУ UUID ЧЕРЕЗ ЗАПЯТУЮ.

    ИДЕАЛЬНО ДЛЯ ФРОНТЕНДА:
    • Простой формат: ?countries=uuid1,uuid2,uuid3
    • Автоматическая валидация
    • Поддержка любых ID полей

    ПРИМЕРЫ:
        ?countries=550e8400-e29b-41d4-a716-446655440000,550e8400-e29b-41d4-a716-446655440001
        ?cities=uuid1,uuid2,uuid3,uuid4
    """

    def filter(self, qs, value):
        if not value:
            return qs

        if isinstance(value, str):
            uuids = []
            for v in value.split(","):
                v = v.strip()
                if v:
                    try:
                        uuid.UUID(v)
                        uuids.append(v)
                    except (ValueError, AttributeError):
                        continue
            value = uuids if uuids else None

        return super().filter(qs, value)


# ====================================================================================
# МОДУЛЬ 2: ОСНОВНОЙ ФИЛЬТР ДЛЯ АДРЕСОВ (УПРОЩЕННЫЙ ДЛЯ ФРОНТЕНДА)
# ====================================================================================

class AddressFilter(FilterSet):
    """
    УПРОЩЕННЫЙ ФИЛЬТР ДЛЯ АДРЕСОВ С УДОБНЫМ API ДЛЯ ФРОНТЕНДА.

    ОСНОВНЫЕ ФИЛЬТРЫ:
    ──────────────────────────────────────────────────────────────────────────────
    1. q (универсальный поиск)     - ?q=Москва Ленина 1
    2. ids (мультивыбор по ID)     - ?ids=uuid1,uuid2,uuid3
    3. countries, regions, cities  - ?countries=uuid1,uuid2&cities=uuid3
    4. has_coordinates, has_index  - ?has_coordinates=true&has_index=false
    5. near (геопоиск)             - ?near=55.7558,37.6173,5
    6. bbox (ограничивающий прямоугольник) - ?bbox=55.5,37.3,56.0,37.9
    7. ordering (сортировка)       - ?ordering=city__name,-street__name

    ВСЕ ПАРАМЕТРЫ ОПЦИОНАЛЬНЫ. МОЖНО КОМБИНИРОВАТЬ ЛЮБЫМ ОБРАЗОМ.
    """

    # ==========================================================================
    # 1. УНИВЕРСАЛЬНЫЙ ПОИСК (ОСНОВНОЙ ПАРАМЕТР ДЛЯ ПОЛЬЗОВАТЕЛЕЙ)
    # ==========================================================================

    q = CharFilter(
        method='universal_search',
        label='Универсальный поиск',
        help_text='Поиск по всем текстовым полям адреса. Пример: ?q=Москва Ленина 1'
    )

    # ==========================================================================
    # 2. МУЛЬТИВЫБОР ПО ID (ИДЕАЛЬНО ДЛЯ ФИЛЬТРОВ НА ФРОНТЕНДЕ)
    # ==========================================================================

    ids = UUIDCommaInFilter(
        field_name='id',
        lookup_expr='in',
        label='Идентификаторы',
        help_text='Фильтрация по нескольким ID через запятую. Пример: ?ids=uuid1,uuid2,uuid3'
    )

    countries = UUIDCommaInFilter(
        field_name='country_id',
        lookup_expr='in',
        label='Страны',
        help_text='Фильтрация по нескольким странам. Пример: ?countries=uuid1,uuid2'
    )

    regions = UUIDCommaInFilter(
        field_name='region_id',
        lookup_expr='in',
        label='Регионы',
        help_text='Фильтрация по нескольким регионам. Пример: ?regions=uuid1,uuid2,uuid3'
    )

    cities = UUIDCommaInFilter(
        field_name='city_id',
        lookup_expr='in',
        label='Города',
        help_text='Фильтрация по нескольким городам. Пример: ?cities=uuid1,uuid2,uuid3,uuid4'
    )

    streets = UUIDCommaInFilter(
        field_name='street_id',
        lookup_expr='in',
        label='Улицы',
        help_text='Фильтрация по нескольким улицам. Пример: ?streets=uuid1,uuid2'
    )

    # ==========================================================================
    # 3. БУЛЕВЫ ФИЛЬТРЫ (ПРОСТЫЕ ПЕРЕКЛЮЧАТЕЛИ ДЛЯ ФРОНТЕНДА)
    # ==========================================================================

    has_coordinates = BooleanFilter(
        method='filter_has_coordinates',
        label='Имеет координаты',
        help_text='Фильтрация по наличию координат. Пример: ?has_coordinates=true'
    )

    has_index = BooleanFilter(
        method='filter_has_index',
        label='Имеет почтовый индекс',
        help_text='Фильтрация по наличию почтового индекса. Пример: ?has_index=false'
    )

    has_house = BooleanFilter(
        field_name='house',
        lookup_expr='isnull',
        exclude=True,
        label='Есть дом',
        help_text='Фильтрация по наличию дома. Пример: ?has_house=true'
    )

    has_street = BooleanFilter(
        field_name='street',
        lookup_expr='isnull',
        exclude=True,
        label='Есть улица',
        help_text='Фильтрация по наличию улицы. Пример: ?has_street=true'
    )

    # ==========================================================================
    # 4. ТЕКСТОВЫЕ ФИЛЬТРЫ (ДЛЯ ТОЧНОГО ПОИСКА)
    # ==========================================================================

    index = CharFilter(
        field_name='index',
        lookup_expr='icontains',
        label='Почтовый индекс',
        help_text='Поиск по почтовому индексу. Пример: ?index=101000'
    )

    index_from = CharFilter(
        field_name='index',
        lookup_expr='gte',
        label='Индекс от',
        help_text='Почтовый индекс от. Пример: ?index_from=100000'
    )

    index_to = CharFilter(
        field_name='index',
        lookup_expr='lte',
        label='Индекс до',
        help_text='Почтовый индекс до. Пример: ?index_to=200000'
    )

    microdistrict = CharFilter(
        field_name='microdistrict',
        lookup_expr='icontains',
        label='Микрорайон',
        help_text='Поиск по микрорайону. Пример: ?microdistrict=Центральный'
    )

    # ==========================================================================
    # 5. ГЕОГРАФИЧЕСКИЕ ФИЛЬТРЫ
    # ==========================================================================

    near = CharFilter(
        method='filter_near',
        label='Близко к точке',
        help_text='Фильтрация по близости к точке. Формат: "широта,долгота,радиус_км". Пример: ?near=55.7558,37.6173,5'
    )

    bbox = CharFilter(
        method='filter_bbox',
        label='Внутри прямоугольника',
        help_text='Фильтрация внутри прямоугольника. Формат: "min_lat,min_lng,max_lat,max_lng". Пример: ?bbox=55.5,37.3,56.0,37.9'
    )

    latitude = NumberFilter(
        field_name='latitude',
        label='Широта',
        help_text='Точная широта. Пример: ?latitude=55.7558'
    )

    longitude = NumberFilter(
        field_name='longitude',
        label='Долгота',
        help_text='Точная долгота. Пример: ?longitude=37.6173'
    )

    # ==========================================================================
    # 6. СОРТИРОВКА
    # ==========================================================================

    ordering = OrderingFilter(
        fields=(
            # Основные поля
            ('country__name', 'country'),
            ('region__name', 'region'),
            ('city__name', 'city'),
            ('street__name', 'street'),
            ('house__number', 'house'),
            ('building__number', 'building'),
            ('index', 'index'),
            ('microdistrict', 'microdistrict'),
            ('latitude', 'latitude'),
            ('longitude', 'longitude'),

            # Комбинированные поля
            ('full_address', 'full_address'),
        ),
        field_labels={
            'country__name': 'Страна',
            'region__name': 'Регион',
            'city__name': 'Город',
            'street__name': 'Улица',
            'house__number': 'Номер дома',
            'building__number': 'Номер строения',
            'index': 'Почтовый индекс',
            'microdistrict': 'Микрорайон',
            'latitude': 'Широта',
            'longitude': 'Долгота',
            'full_address': 'Полный адрес',
        },
        label='Сортировка',
        help_text='Сортировка результатов. Пример: ?ordering=city__name,-street__name'
    )

    class Meta:
        model = Address
        fields = [
            'q', 'ids',
            'countries', 'regions', 'cities', 'streets',
            'has_coordinates', 'has_index', 'has_house', 'has_street',
            'index', 'index_from', 'index_to', 'microdistrict',
            'near', 'bbox', 'latitude', 'longitude',
            'ordering'
        ]

    # ==========================================================================
    # МЕТОДЫ ФИЛЬТРАЦИИ
    # ==========================================================================

    def universal_search(self, queryset, name, value):
        """
        УНИВЕРСАЛЬНЫЙ ПОИСК ПО ВСЕМ ТЕКСТОВЫМ ПОЛЯМ АДРЕСА.

        РАБОТАЕТ С:
        • Страной, регионом, городом, улицей
        • Номером дома и строения
        • Почтовым индексом и микрорайоном
        • Полным адресом

        ОПТИМИЗАЦИЯ:
        • Использует аннотированное поле для поиска
        • Разбивает фразу на слова
        • Ищет совпадения по всем словам

        ПРИМЕРЫ:
        • ?q=Москва Ленина → найдет адреса с "Москва" И "Ленина"
        • ?q=101000 → найдет по почтовому индексу
        • ?q=д 12 → найдет дома с номером 12
        """
        if not value:
            return queryset

        # Аннотируем queryset объединенным текстовым полем
        queryset = queryset.annotate(
            search_text=Concat(
                'country__name', Value(' '),
                'region__name', Value(' '),
                'city__name', Value(' '),
                'street__name', Value(' '),
                'house__number', Value(' '),
                'building__number', Value(' '),
                'microdistrict', Value(' '),
                'index',
                output_field=CharField()
            )
        )

        # Разбиваем поисковую фразу на слова
        words = value.split()
        q_objects = Q()

        for word in words:
            if len(word) >= 2:  # Игнорируем слишком короткие слова
                # Ищем слово в любом поле
                word_q = (
                    Q(search_text__icontains=word) |
                    Q(country__name__icontains=word) |
                    Q(region__name__icontains=word) |
                    Q(city__name__icontains=word) |
                    Q(street__name__icontains=word) |
                    Q(house__number__icontains=word) |
                    Q(building__number__icontains=word) |
                    Q(microdistrict__icontains=word) |
                    Q(index__icontains=word)
                )
                q_objects &= word_q

        return queryset.filter(q_objects).distinct()

    def filter_has_coordinates(self, queryset, name, value):
        """
        ФИЛЬТРАЦИЯ ПО НАЛИЧИЮ КООРДИНАТ.

        true  → только адреса с координатами
        false → только адреса без координат
        null  → все адреса (без фильтрации)
        """
        if value is True:
            return queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False
            )
        elif value is False:
            return queryset.filter(
                Q(latitude__isnull=True) | Q(longitude__isnull=True)
            )
        return queryset

    def filter_has_index(self, queryset, name, value):
        """
        ФИЛЬТРАЦИЯ ПО НАЛИЧИЮ ПОЧТОВОГО ИНДЕКСА.

        true  → только адреса с индексом
        false → только адреса без индекса
        """
        if value is True:
            return queryset.filter(index__isnull=False)
        elif value is False:
            return queryset.filter(index__isnull=True)
        return queryset

    def filter_near(self, queryset, name, value):
        """
        ФИЛЬТРАЦИЯ ПО БЛИЗОСТИ К ТОЧКЕ.

        ФОРМАТ: "широта,долгота,радиус_км"
        ПРИМЕР: "55.7558,37.6173,5" → в радиусе 5 км от центра Москвы

        ЛОГИКА:
        1. Разбираем строку на координаты и радиус
        2. Вычисляем ограничивающий прямоугольник
        3. Фильтруем адреса внутри прямоугольника

        ПРИМЕЧАНИЕ: Для точного расчета расстояний нужен PostGIS.
        """
        try:
            parts = value.split(',')
            if len(parts) != 3:
                return queryset

            lat, lng, radius = float(parts[0]), float(parts[1]), float(parts[2])

            # Упрощенный расчет ограничивающего прямоугольника
            # 1 градус широты ≈ 111 км
            # 1 градус долготы ≈ 111 км * cos(широта)
            from math import cos, radians

            lat_min = lat - (radius / 111.0)
            lat_max = lat + (radius / 111.0)

            # Корректируем для долготы
            lng_degree = 111.0 * abs(cos(radians(lat)))
            lng_min = lng - (radius / lng_degree)
            lng_max = lng + (radius / lng_degree)

            return queryset.filter(
                latitude__gte=lat_min,
                latitude__lte=lat_max,
                longitude__gte=lng_min,
                longitude__lte=lng_max
            )
        except (ValueError, AttributeError, TypeError):
            return queryset

    def filter_bbox(self, queryset, name, value):
        """
        ФИЛЬТРАЦИЯ ВНУТРИ ОГРАНИЧИВАЮЩЕГО ПРЯМОУГОЛЬНИКА.

        ФОРМАТ: "min_lat,min_lng,max_lat,max_lng"
        ПРИМЕР: "55.5,37.3,56.0,37.9" → прямоугольник вокруг Москвы

        ЛОГИКА:
        1. Разбираем строку на координаты
        2. Определяем минимальные и максимальные значения
        3. Фильтруем адреса внутри прямоугольника
        """
        try:
            coords = [float(c.strip()) for c in value.split(',')]
            if len(coords) != 4:
                return queryset

            lat1, lng1, lat2, lng2 = coords
            lat_min, lat_max = sorted([lat1, lat2])
            lng_min, lng_max = sorted([lng1, lng2])

            return queryset.filter(
                latitude__gte=lat_min,
                latitude__lte=lat_max,
                longitude__gte=lng_min,
                longitude__lte=lng_max
            )
        except (ValueError, AttributeError, TypeError):
            return queryset

    @property
    def qs(self):
        """
        ОПТИМИЗАЦИЯ QUERYSET ДЛЯ ВСЕХ ЗАПРОСОВ.

        ДЕЙСТВИЯ:
        1. select_related для всех связанных моделей
        2. Оптимизация только для списковых запросов
        3. Автоматическое ограничение при больших выборках
        """
        queryset = super().qs

        # Оптимизация только для списковых запросов
        if not self.request or 'pk' not in self.request.parser_context.get('kwargs', {}):
            queryset = queryset.select_related(
                'country',
                'federal_district',
                'region',
                'city',
                'administrative_territory',
                'administrative_unit',
                'street',
                'house',
                'building'
            )

        # Автоматическое ограничение при отсутствии фильтров
        # (опционально, для защиты от слишком больших запросов)
        params = dict(self.request.GET) if self.request else {}
        has_filters = any(key not in ['page', 'ordering', 'format'] for key in params.keys())

        if not has_filters:
            # Если нет фильтров, ограничиваем 1000 записей
            MAX_UNFILTERED = 1000
            count = queryset.count()
            if count > MAX_UNFILTERED:
                queryset = queryset[:MAX_UNFILTERED]

        return queryset


# ====================================================================================
# МОДУЛЬ 3: ФИЛЬТРЫ ДЛЯ ОСНОВНЫХ МОДЕЛЕЙ (УПРОЩЕННЫЕ)
# ====================================================================================

class CountryFilter(FilterSet):
    """
    УПРОЩЕННЫЙ ФИЛЬТР ДЛЯ СТРАН.

    ПАРАМЕТРЫ:
    • q - универсальный поиск
    • ids - мультивыбор по ID
    • ordering - сортировка

    ПРИМЕРЫ:
    • GET /api/addresses/countries/?q=Рос
    • GET /api/addresses/countries/?ids=uuid1,uuid2
    • GET /api/addresses/countries/?ordering=name
    """

    q = CharFilter(
        method='search',
        label='Универсальный поиск',
        help_text='Поиск по названию страны. Пример: ?q=Рос'
    )

    ids = UUIDCommaInFilter(
        field_name='id',
        lookup_expr='in',
        label='Идентификаторы',
        help_text='Фильтрация по нескольким ID через запятую'
    )

    ordering = OrderingFilter(
        fields=(('name', 'name'),),
        field_labels={'name': 'Название страны'}
    )

    class Meta:
        model = Country
        fields = ['q', 'ids']

    def search(self, queryset, name, value):
        """Поиск по названию страны."""
        if not value:
            return queryset
        return queryset.filter(name__icontains=value)


class CityFilter(FilterSet):
    """
    УПРОЩЕННЫЙ ФИЛЬТР ДЛЯ ГОРОДОВ.

    ПАРАМЕТРЫ:
    • q - универсальный поиск
    • ids - мультивыбор по ID
    • countries, regions - фильтрация по связанным объектам
    • has_administrative_territory - наличие административных округов
    • ordering - сортировка

    ПРИМЕРЫ:
    • GET /api/addresses/cities/?q=Моск
    • GET /api/addresses/cities/?countries=uuid1&regions=uuid2,uuid3
    • GET /api/addresses/cities/?has_administrative_territory=true&ordering=name
    """

    q = CharFilter(
        method='search',
        label='Универсальный поиск',
        help_text='Поиск по названию города и региону'
    )

    ids = UUIDCommaInFilter(
        field_name='id',
        lookup_expr='in',
        label='Идентификаторы',
        help_text='Фильтрация по нескольким ID через запятую'
    )

    countries = UUIDCommaInFilter(
        field_name='region__federal_district__country_id',
        lookup_expr='in',
        label='Страны',
        help_text='Фильтрация по странам'
    )

    regions = UUIDCommaInFilter(
        field_name='region_id',
        lookup_expr='in',
        label='Регионы',
        help_text='Фильтрация по регионам'
    )

    has_administrative_territory = BooleanFilter(
        field_name='has_administrative_territory',
        label='Наличие административных округов',
        help_text='Фильтрация по наличию административных округов'
    )

    ordering = OrderingFilter(
        fields=(
            ('name', 'name'),
            ('region__name', 'region'),
        ),
        field_labels={
            'name': 'Название города',
            'region__name': 'Регион',
        }
    )

    class Meta:
        model = City
        fields = ['q', 'ids', 'countries', 'regions', 'has_administrative_territory']

    def search(self, queryset, name, value):
        """Универсальный поиск по городам."""
        if not value:
            return queryset

        q = Q(name__icontains=value)
        q |= Q(region__name__icontains=value)
        q |= Q(region__federal_district__name__icontains=value)

        return queryset.filter(q).distinct()


class StreetFilter(FilterSet):
    """
    УПРОЩЕННЫЙ ФИЛЬТР ДЛЯ УЛИЦ.

    ПАРАМЕТРЫ:
    • q - универсальный поиск
    • ids - мультивыбор по ID
    • cities - фильтрация по городам
    • ordering - сортировка

    ПРИМЕРЫ:
    • GET /api/addresses/streets/?q=Ленина
    • GET /api/addresses/streets/?cities=uuid1,uuid2
    • GET /api/addresses/streets/?ordering=city__name,name
    """

    q = CharFilter(
        method='search',
        label='Универсальный поиск',
        help_text='Поиск по названию улицы и городу'
    )

    ids = UUIDCommaInFilter(
        field_name='id',
        lookup_expr='in',
        label='Идентификаторы',
        help_text='Фильтрация по нескольким ID через запятую'
    )

    cities = UUIDCommaInFilter(
        field_name='city_id',
        lookup_expr='in',
        label='Города',
        help_text='Фильтрация по городам'
    )

    ordering = OrderingFilter(
        fields=(
            ('name', 'name'),
            ('city__name', 'city'),
        ),
        field_labels={
            'name': 'Название улицы',
            'city__name': 'Город',
        }
    )

    class Meta:
        model = Street
        fields = ['q', 'ids', 'cities']

    def search(self, queryset, name, value):
        """Универсальный поиск по улицам."""
        if not value:
            return queryset

        q = Q(name__icontains=value)
        q |= Q(city__name__icontains=value)
        q |= Q(street_type__name__icontains=value)

        return queryset.filter(q).distinct()