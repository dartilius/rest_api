"""
Схемы (OpenAPI) для фильтров адресов с актуальным функционалом.

МОДУЛЬ SCHEMAS:
─────────────────────────────────────────────────────────────────────────────────────
Содержит схемы OpenAPI для всех фильтров приложения addresses.
Все схемы соответствуют текущему функционалу, описанному в filters.py.

ТЕКУЩИЙ ФУНКЦИОНАЛ ФИЛЬТРАЦИИ:
─────────────────────────────────────────────────────────────────────────────────────
1. Базовые параметры для всех моделей:
   • search - текстовый поиск по названию
   • ids - фильтр по ID через запятую
   • ordering - сортировка результатов

2. Специфичные параметры для некоторых моделей:
   • Регионы: federal_districts - фильтр по федеральным округам
   • Города: regions, federal_districts - фильтры по регионам и федеральным округам
   • Улицы: cities - фильтр по городам

3. Адреса: только универсальный поиск (search) по всем полям адреса

ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ДЛЯ ФРОНТЕНД-РАЗРАБОТЧИКОВ:
─────────────────────────────────────────────────────────────────────────────────────
1. ПРОСТОЙ ПОИСК:
   GET /api/addresses/addresses/?search=Москва Ленина

2. МУЛЬТИВЫБОР ПО ID:
   GET /api/addresses/addresses/?ids=uuid1,uuid2,uuid3

3. ФИЛЬТРАЦИЯ СТРАН:
   GET /api/addresses/countries/?search=Рос

4. ФИЛЬТРАЦИЯ ГОРОДОВ ПО РЕГИОНАМ:
   GET /api/addresses/cities/?regions=uuid1,uuid2

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
        description='''
        Сортировка результатов.
        
        ФОРМАТ: имя_поля или -имя_поля для обратной сортировки
        
        ПРИМЕРЫ:
        • ?ordering=name → сортировка по названию (A-Z)
        • ?ordering=-name → обратная сортировка по названию (Z-A)
        • ?ordering=city__name,-street__name → сортировка по городу, затем по улице в обратном порядке
        
        ДОСТУПНЫЕ ПОЛЯ ДЛЯ КАЖДОЙ МОДЕЛИ:
        • Страны: name
        • Федеральные округа: name, abbreviated_name
        • Регионы: name, abbreviated_name, federal_district__name
        • Города: name, region__name, region__federal_district__name
        • Улицы: name, city__name
        • Адреса: country__name, region__name, city__name, street__name, house__number, building__number, index, microdistrict
        ''',
        required=False,
        examples=[
            OpenApiExample('По возрастанию', value='name'),
            OpenApiExample('По убыванию', value='-name'),
            OpenApiExample('Сложная сортировка', value='city__name,-street__name'),
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
        
        РЕАЛИЗАЦИЯ:
        Используется OptionalPagination из views.py, которая активируется только при наличии параметра ?page=
        ''',
        required=False,
        examples=[
            OpenApiExample('Страница 1', value=1),
            OpenApiExample('Страница 2', value=2),
            OpenApiExample('Страница 3', value=3),
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
        
        ОГРАНИЧЕНИЯ:
        • Максимальный размер: 1000 записей
        • Минимальный размер: 1 запись
        • По умолчанию: 100 записей
        ''',
        required=False,
        examples=[
            OpenApiExample('10 записей', value=10),
            OpenApiExample('50 записей', value=50),
            OpenApiExample('100 записей', value=100),
            OpenApiExample('200 записей', value=200),
        ]
    ),
]

# ====================================================================================
# МОДУЛЬ 2: ПАРАМЕТРЫ ДЛЯ ФИЛЬТРА АДРЕСОВ (УПРОЩЕННЫЕ)
# ====================================================================================

ADDRESS_FILTER_PARAMETERS = COMMON_FILTER_PARAMETERS + PAGINATION_PARAMETERS + [
    OpenApiParameter(
        name='search',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        УНИВЕРСАЛЬНЫЙ ПОИСК по всем компонентам адреса.
        
        КАК РАБОТАЕТ (логика из AddressFilter.filter_search):
        1. Разбивает поисковую фразу на слова
        2. Ищет совпадения по всем словам одновременно (логическое И)
        3. Игнорирует слова короче 2 символов
        4. Ищет в текстовых полях всех связанных моделей
        
        ПОЛЯ ПОИСКА:
        • Страна: country__name
        • Регион: region__name
        • Город: city__name
        • Улица: street__name
        • Дом: house__number
        • Строение: building__number
        • Микрорайон: microdistrict
        • Почтовый индекс: index
        • Административный округ: administrative_territory__name
        • Административная единица: administrative_unit__name
        
        ПРИМЕРЫ:
        • ?search=Москва → адреса, содержащие "Москва" в любом поле
        • ?search=Ленина 1 → адреса с "Ленина" И "1" (оба слова должны быть найдены)
        • ?search=101000 → поиск по почтовому индексу
        • ?search=д 12 → поиск домов с номером 12
        • ?search=Москва Центральный → адреса Москвы в Центральном микрорайоне
        
        ОСОБЕННОСТИ:
        • Регистронезависимый поиск
        • Частичное совпадение (icontains)
        • Логическое И для нескольких слов
        ''',
        required=False,
        examples=[
            OpenApiExample(
                'Поиск по адресу',
                value='Москва Ленина 1',
                description='Найдет адреса, содержащие все три слова: Москва, Ленина и 1'
            ),
            OpenApiExample(
                'Поиск по индексу',
                value='101000',
                description='Найдет адреса с почтовым индексом 101000'
            ),
            OpenApiExample(
                'Поиск по микрорайону',
                value='Центральный',
                description='Найдет адреса в Центральном микрорайоне'
            ),
            OpenApiExample(
                'Комбинированный поиск',
                value='Санкт-Петербург Невский',
                description='Найдет адреса в Санкт-Петербурге на Невском проспекте'
            ),
        ]
    ),

    OpenApiParameter(
        name='ids',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        ФИЛЬТРАЦИЯ ПО НЕСКОЛЬКИМ ID АДРЕСОВ через запятую.
        
        ФОРМАТ: UUID1,UUID2,UUID3
        
        ПРИМЕРЫ:
        • ?ids=550e8400-e29b-41d4-a716-446655440000 → один адрес
        • ?ids=uuid1,uuid2,uuid3 → несколько адресов
        • ?ids= → пустой параметр (игнорируется)
        
        ВАЛИДАЦИЯ:
        • Некорректные UUID игнорируются
        • Пустые значения пропускаются
        • Минимальная длина UUID: 36 символов
        
        РЕАЛИЗАЦИЯ:
        Использует UUIDCommaInFilter из filters.py
        ''',
        required=False,
        examples=[
            OpenApiExample(
                'Один ID',
                value='550e8400-e29b-41d4-a716-446655440000',
                description='Точный поиск по одному UUID адреса'
            ),
            OpenApiExample(
                'Несколько ID',
                value='uuid1,uuid2,uuid3',
                description='Поиск по нескольким UUID адресов'
            ),
        ]
    ),
]

# ====================================================================================
# МОДУЛЬ 3: ПАРАМЕТРЫ ДЛЯ ДРУГИХ МОДЕЛЕЙ
# ====================================================================================

COUNTRY_FILTER_PARAMETERS = COMMON_FILTER_PARAMETERS + PAGINATION_PARAMETERS + [
    OpenApiParameter(
        name='search',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        ПОИСК ПО НАЗВАНИЮ СТРАНЫ.
        
        ЛОГИКА (из CountryFilter.filter_search):
        • Ищет по полю name
        • Частичное совпадение (icontains)
        • Регистронезависимый поиск
        
        ПРИМЕРЫ:
        • ?search=Рос → найдет "Россия", "Белоруссия"
        • ?search=США → найдет "Соединенные Штаты Америки"
        • ?search=land → найдет "England", "Ireland", "Finland"
        ''',
        required=False,
        examples=[
            OpenApiExample('Поиск России', value='Рос'),
            OpenApiExample('Поиск США', value='США'),
            OpenApiExample('Поиск Германии', value='Герма'),
        ]
    ),

    OpenApiParameter(
        name='ids',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким ID стран через запятую',
        examples=[OpenApiExample('Две страны', value='uuid1,uuid2')]
    ),
]

CITY_FILTER_PARAMETERS = COMMON_FILTER_PARAMETERS + PAGINATION_PARAMETERS + [
    OpenApiParameter(
        name='search',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        ПОИСК ПО ГОРОДАМ.
        
        ЛОГИКА (из CityFilter.filter_search):
        • Ищет по названию города (name)
        • Ищет по названию региона (region__name)
        • Ищет по названию федерального округа (region__federal_district__name)
        • Частичное совпадение (icontains)
        
        ПРИМЕРЫ:
        • ?search=Моск → найдет "Москва"
        • ?search=Санкт → найдет "Санкт-Петербург"
        • ?search=Новоси → найдет "Новосибирск"
        • ?search=Московская → найдет города Московской области
        • ?search=ЦФО → найдет города Центрального федерального округа
        ''',
        required=False,
        examples=[
            OpenApiExample('Поиск Москвы', value='Моск'),
            OpenApiExample('Поиск городов области', value='Московская'),
            OpenApiExample('Поиск по федеральному округу', value='ЦФО'),
        ]
    ),

    OpenApiParameter(
        name='ids',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким ID городов через запятую',
        examples=[OpenApiExample('Три города', value='uuid1,uuid2,uuid3')]
    ),

    OpenApiParameter(
        name='regions',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        ФИЛЬТРАЦИЯ ПО РЕГИОНАМ (UUID через запятую).
        
        ЛОГИКА:
        • Выбирает города, принадлежащие указанным регионам
        • Поддерживает несколько регионов через запятую
        • Использует UUIDCommaInFilter
        
        ПРИМЕРЫ:
        • ?regions=uuid-московская-обл → города Московской области
        • ?regions=uuid1,uuid2 → города двух регионов
        • ?regions= → пустой параметр (игнорируется)
        ''',
        required=False,
        examples=[OpenApiExample('Два региона', value='uuid1,uuid2')]
    ),

    OpenApiParameter(
        name='federal_districts',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        ФИЛЬТРАЦИЯ ПО ФЕДЕРАЛЬНЫМ ОКРУГАМ (UUID через запятую).
        
        ЛОГИКА:
        • Выбирает города, принадлежащие регионам указанных федеральных округов
        • Фильтрация через связь: city → region → federal_district
        • Поддерживает несколько федеральных округов через запятую
        
        ПРИМЕРЫ:
        • ?federal_districts=uuid-цфо → города Центрального федерального округа
        • ?federal_districts=uuid-цфо,uuid-сзфо → города двух федеральных округов
        ''',
        required=False,
        examples=[OpenApiExample('Один федеральный округ', value='uuid-цфо')]
    ),
]

STREET_FILTER_PARAMETERS = COMMON_FILTER_PARAMETERS + PAGINATION_PARAMETERS + [
    OpenApiParameter(
        name='search',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        ПОИСК ПО УЛИЦАМ.
        
        ЛОГИКА (из StreetFilter.filter_search):
        • Ищет по названию улицы (name)
        • Ищет по названию города (city__name)
        • Частичное совпадение (icontains)
        
        ПРИМЕРЫ:
        • ?search=Ленина → найдет улицы с названием "Ленина"
        • ?search=проспект → найдет проспекты
        • ?search=Москва Ленина → найдет улицу Ленина в Москве
        • ?search=Санкт-Петербург Невский → найдет Невский проспект в СПб
        ''',
        required=False,
        examples=[
            OpenApiExample('Поиск улицы', value='Ленина'),
            OpenApiExample('Поиск проспекта', value='проспект'),
            OpenApiExample('Поиск по городу и улице', value='Москва Ленина'),
        ]
    ),

    OpenApiParameter(
        name='ids',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким ID улиц через запятую',
        examples=[OpenApiExample('Две улицы', value='uuid1,uuid2')]
    ),

    OpenApiParameter(
        name='cities',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='''
        ФИЛЬТРАЦИЯ ПО ГОРОДАМ (UUID через запятую).
        
        ЛОГИКА:
        • Выбирает улицы, принадлежащие указанным городам
        • Поддерживает несколько городов через запятую
        • Использует UUIDCommaInFilter
        
        ПРИМЕРЫ:
        • ?cities=uuid-москва → улицы Москвы
        • ?cities=uuid1,uuid2 → улицы двух городов
        • ?cities= → пустой параметр (игнорируется)
        ''',
        required=False,
        examples=[OpenApiExample('Один город', value='uuid-москва')]
    ),
]

# ====================================================================================
# МОДУЛЬ 4: ДЕКОРАТОРЫ ДЛЯ VIEWSETS (ОБНОВЛЕННЫЕ)
# ====================================================================================

def address_list_schema():
    """
    ДЕКОРАТОР ДЛЯ ДОКУМЕНТАЦИИ СПИСКА АДРЕСОВ.

    СООТВЕТСТВУЕТ ТЕКУЩЕМУ ФУНКЦИОНАЛУ AddressFilter.
    """
    return extend_schema(
        summary="Список адресов",
        description="""
        Получение списка адресов с текущей фильтрацией.
        
        ## ТЕКУЩИЙ ФУНКЦИОНАЛ ФИЛЬТРАЦИИ:
        
        ### 1. УНИВЕРСАЛЬНЫЙ ПОИСК (search):
        ```http
        GET /api/addresses/addresses/?search=Москва Ленина
        ```
        • Ищет по всем компонентам адреса
        • Разбивает фразу на слова
        • Требует совпадения по всем словам (логическое И)
        
        ### 2. ФИЛЬТРАЦИЯ ПО ID (ids):
        ```http
        GET /api/addresses/addresses/?ids=uuid1,uuid2,uuid3
        ```
        • Выборка конкретных адресов по UUID
        • Поддерживает несколько ID через запятую
        
        ### 3. ПАГИНАЦИЯ (опциональная):
        ```http
        GET /api/addresses/addresses/ → ВСЕ данные
        GET /api/addresses/addresses/?page=2 → страница 2
        GET /api/addresses/addresses/?page=1&page_size=50 → страница 1, 50 записей
        ```
        
        ## ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:
        
        ### ВСЕ АДРЕСА МОСКВЫ:
        ```http
        GET /api/addresses/addresses/?search=Москва
        ```
        
        ### АДРЕСА НА УЛИЦЕ ЛЕНИНА:
        ```http
        GET /api/addresses/addresses/?search=Ленина
        ```
        
        ### КОНКРЕТНЫЕ АДРЕСА ПО ID:
        ```http
        GET /api/addresses/addresses/?ids=550e8400-e29b-41d4-a716-446655440000,uuid2,uuid3
        ```
        
        ### ПОИСК С СОРТИРОВКОЙ:
        ```http
        GET /api/addresses/addresses/?search=Москва&ordering=street__name
        ```
        
        ### ПАГИНИРОВАННЫЙ ПОИСК:
        ```http
        GET /api/addresses/addresses/?page=1&page_size=20&search=Ленина&ordering=-city__name
        ```
        """,
        parameters=ADDRESS_FILTER_PARAMETERS,
        examples=[
            OpenApiExample(
                'Пример 1: Простой поиск',
                value={
                    'search': 'Москва Ленина',
                    'ordering': 'street__name'
                },
                description='Поиск адресов Москвы на улице Ленина, отсортированных по названию улицы'
            ),
            OpenApiExample(
                'Пример 2: Фильтр по ID',
                value={
                    'ids': 'uuid1,uuid2,uuid3',
                    'ordering': 'city__name'
                },
                description='Конкретные адреса по ID, отсортированные по городу'
            ),
            OpenApiExample(
                'Пример 3: С пагинацией',
                value={
                    'page': 2,
                    'page_size': 50,
                    'search': 'Центральный',
                    'ordering': 'region__name,city__name'
                },
                description='Страница 2 адресов в Центральном микрорайоне, отсортированных по региону и городу'
            ),
        ]
    )


def country_list_schema():
    """Декоратор для документации списка стран."""
    return extend_schema(
        summary="Список стран",
        description="""
        Получение списка стран.
        
        ДОСТУПНЫЕ ФИЛЬТРЫ:
        • search - поиск по названию страны
        • ids - фильтр по ID через запятую
        • ordering - сортировка
        • page, page_size - пагинация (опционально)
        
        ПРИМЕРЫ:
        ```http
        GET /api/addresses/countries/ → все страны
        GET /api/addresses/countries/?search=Рос → поиск стран с "Рос"
        GET /api/addresses/countries/?ids=uuid1,uuid2 → фильтр по ID
        GET /api/addresses/countries/?page=2 → пагинация
        GET /api/addresses/countries/?ordering=-name → сортировка по названию (Z-A)
        ```
        """,
        parameters=COUNTRY_FILTER_PARAMETERS,
        examples=[
            OpenApiExample(
                'Пример без пагинации',
                value={'search': 'Рос', 'ordering': 'name'},
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
        
        ДОСТУПНЫЕ ФИЛЬТРЫ:
        • search - поиск по названию города, региона или федерального округа
        • ids - фильтр по ID через запятую
        • regions - фильтр по регионам (UUID через запятую)
        • federal_districts - фильтр по федеральным округам (UUID через запятую)
        • ordering - сортировка
        • page, page_size - пагинация (опционально)
        
        ПРИМЕРЫ:
        ```http
        GET /api/addresses/cities/ → все города
        GET /api/addresses/cities/?search=Моск → поиск городов
        GET /api/addresses/cities/?ids=uuid1,uuid2,uuid3 → фильтр по ID
        GET /api/addresses/cities/?regions=uuid1,uuid2 → города регионов
        GET /api/addresses/cities/?federal_districts=uuid-цфо → города ЦФО
        GET /api/addresses/cities/?page=2 → пагинация
        ```
        
        ОСОБЕННОСТИ ПОИСКА:
        • Ищет по названию города
        • Ищет по названию региона
        • Ищет по названию федерального округа
        """,
        parameters=CITY_FILTER_PARAMETERS,
        examples=[
            OpenApiExample(
                'Пример фильтрации',
                value={
                    'regions': 'uuid1,uuid2',
                    'ordering': 'name',
                    'page': 1,
                    'page_size': 50
                },
                description='Города двух регионов, отсортированные по названию, страница 1, 50 записей'
            ),
        ]
    )


def street_list_schema():
    """Декоратор для документации списка улиц."""
    return extend_schema(
        summary="Список улиц",
        description="""
        Получение списка улиц.
        
        ДОСТУПНЫЕ ФИЛЬТРЫ:
        • search - поиск по названию улицы или города
        • ids - фильтр по ID через запятую
        • cities - фильтр по городам (UUID через запятую)
        • ordering - сортировка
        • page, page_size - пагинация (опционально)
        
        ПРИМЕРЫ:
        ```http
        GET /api/addresses/streets/ → все улицы
        GET /api/addresses/streets/?search=Ленина → поиск улиц
        GET /api/addresses/streets/?ids=uuid1,uuid2 → фильтр по ID
        GET /api/addresses/streets/?cities=uuid1,uuid2 → улицы городов
        GET /api/addresses/streets/?page=2&page_size=100 → пагинация
        ```
        
        ОСОБЕННОСТИ ПОИСКА:
        • Ищет по названию улицы
        • Ищет по названию города
        """,
        parameters=STREET_FILTER_PARAMETERS,
        examples=[
            OpenApiExample(
                'Пример с фильтрами',
                value={
                    'cities': 'uuid1,uuid2',
                    'search': 'проспект',
                    'ordering': 'city__name,name',
                    'page': 1,
                    'page_size': 100
                },
                description='Проспекты в двух городах, отсортированные по городу и названию, страница 1'
            ),
        ]
    )


# ====================================================================================
# МОДУЛЬ 5: ПАРАМЕТРЫ ДЛЯ ОСТАЛЬНЫХ МОДЕЛЕЙ (БАЗОВЫЕ)
# ====================================================================================

# Для всех остальных моделей используются только базовые параметры:
# FederalDistrict, TypeRegion, Timezone, Region, LocalityType,
# AdministrativeTerritory, AdministrativeTerritorialUnit, StreetType,
# House, Building, Coordinates

BASIC_FILTER_PARAMETERS = COMMON_FILTER_PARAMETERS + PAGINATION_PARAMETERS + [
    OpenApiParameter(
        name='search',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по названию (или основному текстовому полю)',
        required=False
    ),
    OpenApiParameter(
        name='ids',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по нескольким ID через запятую',
        required=False
    ),
]