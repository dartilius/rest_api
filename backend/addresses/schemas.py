"""
Схемы (OpenAPI) для фильтров адресов с полной документацией.

МОДУЛЬ SCHEMAS:
─────────────────────────────────────────────────────────────────────────────────────
Содержит схемы OpenAPI для всех фильтров приложения addresses.
Все схемы включают подробные описания и примеры использования.

ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ДЛЯ ФРОНТЕНД-РАЗРАБОТЧИКОВ:
─────────────────────────────────────────────────────────────────────────────────────
1. ПРОСТОЙ ПОИСК:
   GET /api/addresses/addresses/?q=Москва Ленина

2. МУЛЬТИВЫБОР:
   GET /api/addresses/addresses/?countries=uuid1,uuid2&cities=uuid3,uuid4

3. ФИЛЬТРЫ ПО НАЛИЧИЮ:
   GET /api/addresses/addresses/?has_coordinates=true&has_index=false

4. ГЕОПОИСК:
   GET /api/addresses/addresses/?near=55.7558,37.6173,5

5. ПАГИНАЦИЯ (ОПЦИОНАЛЬНО):
   GET /api/addresses/addresses/?page=2&page_size=50

6. СОРТИРОВКА:
   GET /api/addresses/addresses/?ordering=city__name,-street__name
"""

from drf_spectacular.utils import OpenApiParameter, OpenApiExample, extend_schema
from drf_spectacular.types import OpenApiTypes

# ====================================================================================
# МОДУЛЬ 1: ОБЩИЕ ПАРАМЕТРЫ ДЛЯ ВСЕХ ФИЛЬТРОВ
# ====================================================================================

COMMON_FILTER_PARAMETERS = [
    OpenApiParameter(
        name='ordering',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Сортировка результатов',
        examples=[
            OpenApiExample('По названию страны', value='country__name'),
            OpenApiExample('По городу и улице', value='city__name,-street__name'),
            OpenApiExample('По индексу', value='index'),
        ]
    ),
]

PAGINATION_PARAMETERS = [
    OpenApiParameter(
        name='page',
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description='''
        Номер страницы для пагинации.
        
        📌 ВАЖНО: Пагинация отключена по умолчанию!
        Без параметра ?page= возвращаются ВСЕ данные.
        
        Примеры:
        • ?page=2 → включает пагинацию (страница 2)
        • Без ?page= → все данные без пагинации
        ''',
        required=False,
        examples=[
            OpenApiExample('Страница 2', value=2),
            OpenApiExample('Страница 1', value=1),
        ]
    ),
    OpenApiParameter(
        name='page_size',
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description='''
        Размер страницы при использовании пагинации.
        
        РАБОТАЕТ ТОЛЬКО С ПАРАМЕТРОМ ?page=
        
        Примеры:
        • ?page=1&page_size=50 → страница 1, 50 записей
        • ?page=2&page_size=100 → страница 2, 100 записей
        • Без ?page= → параметр игнорируется
        ''',
        required=False,
        examples=[
            OpenApiExample('50 записей', value=50),
            OpenApiExample('100 записей', value=100),
            OpenApiExample('200 записей', value=200),
        ]
    ),
]

# ====================================================================================
# МОДУЛЬ 2: ПАРАМЕТРЫ ДЛЯ ФИЛЬТРА АДРЕСОВ
# ====================================================================================

ADDRESS_FILTER_PARAMETERS = COMMON_FILTER_PARAMETERS + PAGINATION_PARAMETERS + [
    # 1. УНИВЕРСАЛЬНЫЙ ПОИСК
    OpenApiParameter(
        name='q',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        Универсальный поиск по всем текстовым полям адреса.
        
        КАК РАБОТАЕТ:
        • Ищет по стране, региону, городу, улице, дому, индексу, микрорайону
        • Разбивает фразу на слова
        • Ищет совпадения по всем словам
        
        ПРИМЕРЫ:
        • ?q=Москва → адреса с "Москва"
        • ?q=Ленина 1 → адреса с "Ленина" И "1"
        • ?q=101000 → поиск по почтовому индексу
        • ?q=д 12 → поиск домов с номером 12
        ''',
        examples=[
            OpenApiExample('Поиск по адресу', value='Москва Ленина 1'),
            OpenApiExample('Поиск по индексу', value='101000'),
            OpenApiExample('Поиск по дому', value='д 12А'),
        ]
    ),

    # 2. МУЛЬТИВЫБОР ПО ID
    OpenApiParameter(
        name='ids',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким ID адресов через запятую',
        examples=[
            OpenApiExample('Один ID', value='550e8400-e29b-41d4-a716-446655440000'),
            OpenApiExample('Несколько ID', value='uuid1,uuid2,uuid3'),
        ]
    ),

    OpenApiParameter(
        name='countries',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким странам (UUID через запятую)',
        examples=[OpenApiExample('Две страны', value='uuid1,uuid2')]
    ),

    OpenApiParameter(
        name='regions',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким регионам (UUID через запятую)',
        examples=[OpenApiExample('Три региона', value='uuid1,uuid2,uuid3')]
    ),

    OpenApiParameter(
        name='cities',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким городам (UUID через запятую)',
        examples=[OpenApiExample('Четыре города', value='uuid1,uuid2,uuid3,uuid4')]
    ),

    OpenApiParameter(
        name='streets',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким улицам (UUID через запятую)',
        examples=[OpenApiExample('Две улицы', value='uuid1,uuid2')]
    ),

    # 3. БУЛЕВЫ ФИЛЬТРЫ
    OpenApiParameter(
        name='has_coordinates',
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        description='''
        Фильтрация по наличию координат.
        
        true  → только адреса с координатами
        false → только адреса без координат
        
        Пример: ?has_coordinates=true
        ''',
        examples=[
            OpenApiExample('С координатами', value=True),
            OpenApiExample('Без координат', value=False),
        ]
    ),

    OpenApiParameter(
        name='has_index',
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по наличию почтового индекса',
        examples=[
            OpenApiExample('С индексом', value=True),
            OpenApiExample('Без индекса', value=False),
        ]
    ),

    OpenApiParameter(
        name='has_house',
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по наличию дома',
        examples=[OpenApiExample('С домом', value=True)]
    ),

    OpenApiParameter(
        name='has_street',
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по наличию улицы',
        examples=[OpenApiExample('С улицей', value=True)]
    ),

    # 4. ПОЧТОВЫЙ ИНДЕКС
    OpenApiParameter(
        name='index',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по почтовому индексу',
        examples=[OpenApiExample('Индекс 101000', value='101000')]
    ),

    OpenApiParameter(
        name='index_from',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Почтовый индекс от',
        examples=[OpenApiExample('От 100000', value='100000')]
    ),

    OpenApiParameter(
        name='index_to',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Почтовый индекс до',
        examples=[OpenApiExample('До 200000', value='200000')]
    ),

    OpenApiParameter(
        name='microdistrict',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по микрорайону',
        examples=[OpenApiExample('Центральный', value='Центральный')]
    ),

    # 5. ГЕОГРАФИЧЕСКИЕ ФИЛЬТРЫ
    OpenApiParameter(
        name='near',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        Фильтрация по близости к точке.
        
        ФОРМАТ: "широта,долгота,радиус_км"
        
        ПРИМЕРЫ:
        • ?near=55.7558,37.6173,5 → в радиусе 5 км от центра Москвы
        • ?near=59.9343,30.3351,2 → в радиусе 2 км от центра СПб
        
        ПРИМЕЧАНИЕ: Упрощенный расчет, для точного нужен PostGIS.
        ''',
        examples=[
            OpenApiExample('5 км от Москвы', value='55.7558,37.6173,5'),
            OpenApiExample('2 км от СПб', value='59.9343,30.3351,2'),
        ]
    ),

    OpenApiParameter(
        name='bbox',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        Фильтрация внутри ограничивающего прямоугольника.
        
        ФОРМАТ: "min_lat,min_lng,max_lat,max_lng"
        
        ПРИМЕР:
        • ?bbox=55.5,37.3,56.0,37.9 → прямоугольник вокруг Москвы
        ''',
        examples=[OpenApiExample('Прямоугольник Москвы', value='55.5,37.3,56.0,37.9')]
    ),

    OpenApiParameter(
        name='latitude',
        type=OpenApiTypes.FLOAT,
        location=OpenApiParameter.QUERY,
        description='Точная широта',
        examples=[OpenApiExample('Широта Москвы', value=55.7558)]
    ),

    OpenApiParameter(
        name='longitude',
        type=OpenApiTypes.FLOAT,
        location=OpenApiParameter.QUERY,
        description='Точная долгота',
        examples=[OpenApiExample('Долгота Москвы', value=37.6173)]
    ),
]

# ====================================================================================
# МОДУЛЬ 3: ПАРАМЕТРЫ ДЛЯ ДРУГИХ МОДЕЛЕЙ
# ====================================================================================

COUNTRY_FILTER_PARAMETERS = COMMON_FILTER_PARAMETERS + PAGINATION_PARAMETERS + [
    OpenApiParameter(
        name='q',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по названию страны',
        examples=[OpenApiExample('Название страны', value='Россия')]
    ),

    OpenApiParameter(
        name='ids',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким ID стран',
        examples=[OpenApiExample('Две страны', value='uuid1,uuid2')]
    ),
]

CITY_FILTER_PARAMETERS = COMMON_FILTER_PARAMETERS + PAGINATION_PARAMETERS + [
    OpenApiParameter(
        name='q',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по названию города или региона',
        examples=[OpenApiExample('Название города', value='Москва')]
    ),

    OpenApiParameter(
        name='ids',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким ID городов',
        examples=[OpenApiExample('Три города', value='uuid1,uuid2,uuid3')]
    ),

    OpenApiParameter(
        name='countries',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по странам',
        examples=[OpenApiExample('Одна страна', value='uuid1')]
    ),

    OpenApiParameter(
        name='regions',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по регионам',
        examples=[OpenApiExample('Два региона', value='uuid1,uuid2')]
    ),

    OpenApiParameter(
        name='has_administrative_territory',
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        description='Наличие административных округов',
        examples=[OpenApiExample('С округами', value=True)]
    ),
]

STREET_FILTER_PARAMETERS = COMMON_FILTER_PARAMETERS + PAGINATION_PARAMETERS + [
    OpenApiParameter(
        name='q',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по названию улицы или города',
        examples=[OpenApiExample('Название улицы', value='Ленина')]
    ),

    OpenApiParameter(
        name='ids',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким ID улиц',
        examples=[OpenApiExample('Две улицы', value='uuid1,uuid2')]
    ),

    OpenApiParameter(
        name='cities',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по городам',
        examples=[OpenApiExample('Один город', value='uuid1')]
    ),
]

# ====================================================================================
# МОДУЛЬ 4: ДЕКОРАТОРЫ ДЛЯ VIEWSETS
# ====================================================================================

def address_list_schema():
    """
    ДЕКОРАТОР ДЛЯ ДОКУМЕНТАЦИИ СПИСКА АДРЕСОВ.
    """
    return extend_schema(
        summary="Список адресов",
        description="""
        Получение списка адресов с расширенной фильтрацией.
        
        ## 📌 ОСОБЕННОСТИ ПАГИНАЦИИ:
        
        ### 1. БЕЗ ПАГИНАЦИИ (ПО УМОЛЧАНИЮ):
        ```http
        GET /api/addresses/addresses/
        GET /api/addresses/addresses/?q=Москва
        GET /api/addresses/addresses/?countries=uuid1,uuid2
        ```
        
        **Возвращает:** Все найденные адреса
        
        ### 2. С ПАГИНАЦИЕЙ (ЕСЛИ НУЖНО):
        ```http
        GET /api/addresses/addresses/?page=2
        GET /api/addresses/addresses/?page=1&page_size=50
        GET /api/addresses/addresses/?page=2&page_size=100&q=Ленина
        ```
        
        **Возвращает:** Только одну страницу результатов
        
        ## 🎯 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:
        
        ### ВСЕ АДРЕСА МОСКВЫ:
        ```http
        GET /api/addresses/addresses/?q=Москва
        ```
        
        ### АДРЕСА В НЕСКОЛЬКИХ СТРАНАХ С КООРДИНАТАМИ:
        ```http
        GET /api/addresses/addresses/?countries=uuid1,uuid2&has_coordinates=true
        ```
        
        ### ГЕОПОИСК (В РАДИУСЕ 5 КМ):
        ```http
        GET /api/addresses/addresses/?near=55.7558,37.6173,5
        ```
        
        ### СОРТИРОВКА ПО ГОРОДУ И УЛИЦЕ:
        ```http
        GET /api/addresses/addresses/?ordering=city__name,-street__name
        ```
        
        ### ПАГИНИРОВАННЫЙ ПОИСК:
        ```http
        GET /api/addresses/addresses/?page=1&page_size=20&q=Ленина&has_index=true
        ```
        """,
        parameters=ADDRESS_FILTER_PARAMETERS,
        examples=[
            OpenApiExample(
                'Пример 1: Без пагинации',
                value={
                    'q': 'Москва Ленина',
                    'has_coordinates': True,
                    'ordering': 'street__name'
                },
                description='Все адреса Москвы на улице Ленина с координатами'
            ),
            OpenApiExample(
                'Пример 2: С пагинацией',
                value={
                    'page': 2,
                    'page_size': 50,
                    'countries': 'uuid1,uuid2',
                    'has_index': True
                },
                description='Страница 2 адресов двух стран с почтовым индексом'
            ),
            OpenApiExample(
                'Пример 3: Геопоиск',
                value={
                    'near': '55.7558,37.6173,5',
                    'has_coordinates': True
                },
                description='Адреса в радиусе 5 км от центра Москвы'
            ),
        ]
    )


def country_list_schema():
    """Декоратор для документации списка стран."""
    return extend_schema(
        summary="Список стран",
        description="""
        Получение списка стран.
        
        ПРИМЕРЫ:
        ```http
        GET /api/addresses/countries/ → все страны
        GET /api/addresses/countries/?q=Рос → поиск
        GET /api/addresses/countries/?ids=uuid1,uuid2 → фильтр по ID
        GET /api/addresses/countries/?page=2 → пагинация
        ```
        """,
        parameters=COUNTRY_FILTER_PARAMETERS,
        examples=[
            OpenApiExample(
                'Пример без пагинации',
                value={'q': 'Рос', 'ordering': 'name'},
                description='Поиск стран с "Рос", отсортированных по названию'
            ),
        ]
    )


def city_list_schema():
    """Декоратор для документации списка городов."""
    return extend_schema(
        summary="Список городов",
        description="""
        Получение списка городов.
        
        ПРИМЕРЫ:
        ```http
        GET /api/addresses/cities/ → все города
        GET /api/addresses/cities/?q=Моск → поиск
        GET /api/addresses/cities/?countries=uuid1 → города страны
        GET /api/addresses/cities/?regions=uuid1,uuid2 → города регионов
        GET /api/addresses/cities/?page=2 → пагинация
        ```
        """,
        parameters=CITY_FILTER_PARAMETERS,
        examples=[
            OpenApiExample(
                'Пример фильтрации',
                value={
                    'countries': 'uuid1',
                    'has_administrative_territory': True,
                    'ordering': 'name'
                },
                description='Города страны с административными округами'
            ),
        ]
    )


def street_list_schema():
    """Декоратор для документации списка улиц."""
    return extend_schema(
        summary="Список улиц",
        description="""
        Получение списка улиц.
        
        ПРИМЕРЫ:
        ```http
        GET /api/addresses/streets/ → все улицы
        GET /api/addresses/streets/?q=Ленина → поиск
        GET /api/addresses/streets/?cities=uuid1,uuid2 → улицы городов
        GET /api/addresses/streets/?page=2&page_size=100 → пагинация
        ```
        """,
        parameters=STREET_FILTER_PARAMETERS,
        examples=[
            OpenApiExample(
                'Пример с фильтрами',
                value={
                    'cities': 'uuid1,uuid2',
                    'q': 'проспект',
                    'ordering': 'city__name,name'
                },
                description='Проспекты в двух городах, отсортированные'
            ),
        ]
    )