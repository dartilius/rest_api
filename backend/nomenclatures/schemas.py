"""
Схемы (OpenAPI) для фильтров номенклатур с адресами (обновленная версия).

МОДУЛЬ SCHEMAS:
─────────────────────────────────────────────────────────────────────────────────────
Схемы OpenAPI для фильтров номенклатур с короткими именами параметров для адресов.
"""

from drf_spectacular.utils import OpenApiParameter, OpenApiExample, extend_schema
from drf_spectacular.types import OpenApiTypes

# ====================================================================================
# МОДУЛЬ: ПАРАМЕТРЫ ФИЛЬТРАЦИИ ДЛЯ НОМЕНКЛАТУР С АДРЕСАМИ (КОРОТКИЕ ИМЕНА)
# ====================================================================================

NOMENCLATURE_ADDRESS_PARAMETERS = [
    # Основные параметры фильтрации номенклатур
    OpenApiParameter(
        name='search',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Универсальный поиск по всем полям номенклатуры и адреса',
        examples=[
            OpenApiExample(
                'Поиск по названию и адресу',
                value='Москва Станция'
            ),
        ]
    ),

    # Параметры статуса
    OpenApiParameter(
        name='status',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по статусу номенклатуры (0=Online, 1=Offline 5+ minutes, 2=Offline 1+ hour, null=без статуса)',
        examples=[
            OpenApiExample(
                'Онлайн номенклатуры',
                value='0'
            ),
        ]
    ),

    # Параметры бренда и юр.лица
    OpenApiParameter(
        name='brand_id',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по бренду (UUID через запятую)',
        examples=[
            OpenApiExample(
                'Несколько брендов',
                value='uuid1,uuid2'
            ),
        ]
    ),
    OpenApiParameter(
        name='brand_name',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по названию бренда',
    ),
    OpenApiParameter(
        name='legal_entity_name',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по названию юридического лица',
    ),
    OpenApiParameter(
        name='type_of_place',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Тип места размещения',
    ),

    # ==========================================================================
    # ПАРАМЕТРЫ АДРЕСА (КОРОТКИЕ ИМЕНА)
    # ==========================================================================

    # UUID фильтры для адресов
    OpenApiParameter(
        name='address_id',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по ID адресов (UUID через запятую)',
    ),

    # Страна
    OpenApiParameter(
        name='country',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по ID стран (UUID через запятую)',
        examples=[
            OpenApiExample(
                'Несколько стран',
                value='uuid_россии,uuid_казахстана'
            ),
        ]
    ),
    OpenApiParameter(
        name='country_name',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по названию стран (через запятую)',
        examples=[
            OpenApiExample(
                'Несколько стран',
                value='Россия,Казахстан'
            ),
        ]
    ),

    # Регион
    OpenApiParameter(
        name='region',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по ID регионов (UUID через запятую)',
    ),
    OpenApiParameter(
        name='region_name',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по названию регионов (через запятую)',
        examples=[
            OpenApiExample(
                'Несколько регионов',
                value='Московская область,Ленинградская область'
            ),
        ]
    ),

    # Город (основной параметр для фронтенда)
    OpenApiParameter(
        name='city',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по ID городов (UUID через запятую)',
    ),
    OpenApiParameter(
        name='city_name',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по названию городов (через запятую)',
        examples=[
            OpenApiExample(
                'Несколько городов',
                value='Москва,Санкт-Петербург'
            ),
            OpenApiExample(
                'Один город',
                value='Москва'
            ),
        ]
    ),
    OpenApiParameter(
        name='city_name_contains',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по части названия города',
        examples=[
            OpenApiExample(
                'Часть названия',
                value='Моск'
            ),
        ]
    ),

    # Улица
    OpenApiParameter(
        name='street',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Фильтрация по ID улиц (UUID через запятую)',
    ),
    OpenApiParameter(
        name='street_name',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по названию улиц (через запятую)',
        examples=[
            OpenApiExample(
                'Несколько улиц',
                value='Ленина,Победы,Мира'
            ),
        ]
    ),
    OpenApiParameter(
        name='street_name_contains',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по части названия улицы',
    ),

    # Дом
    OpenApiParameter(
        name='house_number',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по номерам домов (через запятую)',
        examples=[
            OpenApiExample(
                'Несколько номеров',
                value='1,12,15А'
            ),
        ]
    ),

    # Почтовый индекс
    OpenApiParameter(
        name='index',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по почтовым индексам (через запятую)',
        examples=[
            OpenApiExample(
                'Несколько индексов',
                value='101000,102000'
            ),
        ]
    ),

    # Микрорайон
    OpenApiParameter(
        name='microdistrict',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Поиск по микрорайонам (через запятую)',
        examples=[
            OpenApiExample(
                'Несколько микрорайонов',
                value='Центральный,Северный'
            ),
        ]
    ),

    # Булевы фильтры
    OpenApiParameter(
        name='has_address',
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        description='Только номенклатуры с привязанным адресом',
        examples=[
            OpenApiExample(
                'Только с адресом',
                value='true'
            ),
            OpenApiExample(
                'Только без адреса',
                value='false'
            ),
        ]
    ),
    OpenApiParameter(
        name='has_index',
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        description='Только адреса с почтовым индексом',
        examples=[
            OpenApiExample(
                'С индексом',
                value='true'
            ),
        ]
    ),
    OpenApiParameter(
        name='has_house',
        type=OpenApiTypes.BOOL,
        location=OpenApiParameter.QUERY,
        description='Только адреса с указанным домом',
    ),

    # Сортировка
    OpenApiParameter(
        name='ordering',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Сортировка результатов (префикс "-" для обратного порядка)',
        examples=[
            OpenApiExample(
                'По названию (А-Я)',
                value='name'
            ),
            OpenApiExample(
                'По цене (дорогие сначала)',
                value='-pricePerMonth'
            ),
            OpenApiExample(
                'По городу и названию',
                value='city,name'
            ),
            OpenApiExample(
                'По стране и цене',
                value='country,-pricePerMonth'
            ),
        ]
    ),
]


def nomenclature_list_schema():
    """
    ДЕКОРАТОР ДЛЯ ДОКУМЕНТАЦИИ СПИСКА НОМЕНКЛАТУР С АДРЕСАМИ.

    Обновленная версия с короткими именами параметров.
    """
    return extend_schema(
        summary="Список номенклатур с фильтрацией по адресам",
        description="""
        Получение списка номенклатур с расширенной фильтрацией, включая адреса.
        
        ## 🎯 Ключевые особенности:
        
        ### Короткие имена параметров:
        • `city_name` вместо `address_city_name`
        • `country` вместо `address_country`
        • `street_name` вместо `address_street_name`
        
        ### Поддержка множественных значений через запятую:
        • `city_name=Москва,Санкт-Петербург`
        • `street_name=Ленина,Победы,Мира`
        • `index=101000,102000,103000`
        
        ## 📋 Основные фильтры:
        
        ### 1. Универсальный поиск:
        - `search` - ищет по всем полям номенклатур и адресов
        
        ### 2. Фильтры номенклатур:
        - `status` - статус доступности (0, 1, 2, null)
        - `brand_name`, `legal_entity_name` - поиск по связанным сущностям
        - `type_of_place` - тип места размещения
        
        ### 3. Новые фильтры по адресам:
        
        #### Фильтры по UUID:
        - `country`, `region`, `city`, `street` - фильтрация по ID
        
        #### Текстовые фильтры (через запятую):
        - `country_name`, `region_name`, `city_name`, `street_name`
        - `house_number`, `index`, `microdistrict`
        
        #### Поиск по части названия:
        - `city_name_contains`, `street_name_contains`
        
        #### Булевы фильтры:
        - `has_address` - есть ли адрес
        - `has_index` - есть ли почтовый индекс
        - `has_house` - есть ли номер дома
        
        ### 4. Сортировка:
        - `ordering` - сортировка по любым полям
        
        ## 🚀 Примеры запросов:
        
        ### Простые запросы:
        ```http
        # Номенклатуры в Москве или СПб
        GET /api/nomenclatures/?city_name=Москва,Санкт-Петербург
        
        # Номенклатуры на улице Ленина или Победы
        GET /api/nomenclatures/?street_name=Ленина,Победы
        
        # Онлайн номенклатуры с адресом
        GET /api/nomenclatures/?status=0&has_address=true
        ```
        
        ### Средние запросы:
        ```http
        # Номенклатуры в России с индексом
        GET /api/nomenclatures/?country_name=Россия&has_index=true
        
        # Поиск по части названия города
        GET /api/nomenclatures/?city_name_contains=Моск
        
        # Сортировка по городу и цене
        GET /api/nomenclatures/?ordering=city,-pricePerMonth
        ```
        
        ### Сложные запросы:
        ```http
        # Номенклатуры от Ростелеком в Москве на улице Ленина
        GET /api/nomenclatures/?brand_name=Ростелеком&city_name=Москва&street_name=Ленина
        
        # Онлайн кафе с адресом и индексом в центральном микрорайоне
        GET /api/nomenclatures/?status=0&type_of_place=кафе&has_address=true&has_index=true&microdistrict=Центральный
        
        # Универсальный поиск с фильтрацией
        GET /api/nomenclatures/?search=Станция Москва&country_name=Россия&ordering=-created
        ```
        
        ### Получение без адреса:
        ```http
        # Все номенклатуры без привязанного адреса
        GET /api/nomenclatures/?has_address=false
        
        # Онлайн номенклатуры без индекса
        GET /api/nomenclatures/?status=0&has_index=false
        ```
        """,
        parameters=NOMENCLATURE_ADDRESS_PARAMETERS,
        examples=[
            OpenApiExample(
                'Пример 1: Фильтрация по городу и статусу',
                value={
                    'city_name': 'Москва',
                    'status': '0',
                    'ordering': 'name',
                    'has_address': True
                },
                description='Онлайн номенклатуры в Москве с адресом, отсортированные по названию'
            ),
            OpenApiExample(
                'Пример 2: Поиск по нескольким городам и улицам',
                value={
                    'city_name': 'Москва,Санкт-Петербург',
                    'street_name': 'Ленина,Победы',
                    'has_address': True,
                    'ordering': 'city,street'
                },
                description='Номенклатуры в Москве или СПб на улице Ленина или Победы'
            ),
            OpenApiExample(
                'Пример 3: Фильтрация по стране и наличию индекса',
                value={
                    'country_name': 'Россия',
                    'has_index': True,
                    'has_house': True,
                    'ordering': '-pricePerMonth'
                },
                description='Номенклатуры в России с почтовым индексом и номером дома, отсортированные по цене (дорогие сначала)'
            ),
            OpenApiExample(
                'Пример 4: Универсальный поиск с булевыми фильтрами',
                value={
                    'search': 'кофе центр',
                    'city_name': 'Москва',
                    'has_address': True,
                    'has_index': True,
                    'ordering': 'street_name,name'
                },
                description='Поиск номенклатур с "кофе" и "центр" в Москве с полным адресом'
            ),
            OpenApiExample(
                'Пример 5: Поиск по части названия и типу',
                value={
                    'city_name_contains': 'Моск',
                    'type_of_place': 'кафе,ресторан',
                    'status': '0',
                    'ordering': 'microdistrict,pricePerMonth'
                },
                description='Онлайн кафе и рестораны в городах с "Моск" в названии'
            ),
        ]
    )