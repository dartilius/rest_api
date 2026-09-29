"""
OpenAPI схемы для документации API адресов.

Здесь описаны ВСЕ возможные параметры, запросы и ответы для каждого эндпоинта.
Эта информация отображается в Swagger UI (/api/docs/) и в ReDoc (/api/redoc/).
"""

from drf_spectacular.utils import OpenApiParameter, OpenApiExample, extend_schema
from drf_spectacular.types import OpenApiTypes

# ══════════════════════════════════════════════════════════════════════════════════
# ОБЩИЕ ПАРАМЕТРЫ (используются почти везде)
# ══════════════════════════════════════════════════════════════════════════════════

COMMON_PARAMETERS = [
    OpenApiParameter(
        name="search",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description=(
            "Поиск по текстовым полям.\n\n"
            "Ищет вхождение подстроки без учёта регистра.\n"
            "Набор полей зависит от модели:\n"
            "- Страны: name, iso_code_2, iso_code_3\n"
            "- Адм. единицы: name, code\n"
            "- Нас. пункты: name, postal_code\n"
            "- Улицы: name, locality__name\n"
            "- Дома: number, street__name\n"
            "- Адреса: ВСЕ компоненты (страна, город, улица, дом, индекс...)\n\n"
            "Примеры:\n"
            "- ?search=Москва\n"
            "- ?search=Ленина"
        ),
    ),
    OpenApiParameter(
        name="ids",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description=(
            "Фильтр по списку UUID через запятую.\n\n"
            "Позволяет получить несколько конкретных записей за один запрос.\n"
            "Некорректные UUID в списке игнорируются.\n\n"
            "Пример: ?ids=550e8400-e29b-41d4-a716-446655440000,550e8400-e29b-41d4-a716-446655440001"
        ),
    ),
    OpenApiParameter(
        name="ordering",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description=(
            "Сортировка результатов.\n\n"
            "Доступные поля зависят от модели.\n"
            'Префикс "-" для сортировки по убыванию.\n\n'
            "Примеры:\n"
            "- ?ordering=name — по имени (А→Я)\n"
            "- ?ordering=-created — сначала новые"
        ),
    ),
]

PAGINATION_PARAMETERS = [
    OpenApiParameter(
        name="page",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description=(
            "Номер страницы для постраничной навигации.\n\n"
            "ВАЖНО: Если параметр НЕ указан — возвращаются ВСЕ записи без пагинации.\n"
            "Если указан — включается пагинация.\n\n"
            "Пример: ?page=1 — первая страница"
        ),
        required=False,
    ),
    OpenApiParameter(
        name="limit",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description=(
            "Размер страницы (работает только вместе с ?page=).\n"
            "По умолчанию: 100\n"
            "Максимум: 1000\n\n"
            "Пример: ?page=1&limit=50"
        ),
        required=False,
    ),
]


# ══════════════════════════════════════════════════════════════════════════════════
# ПРИМЕРЫ ОТВЕТОВ (успешных и ошибочных)
# ══════════════════════════════════════════════════════════════════════════════════

# --- Успешные ответы ---

COUNTRY_EXAMPLE = OpenApiExample(
    name="Страна (200)",
    description="Пример ответа со всеми полями страны",
    value={
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Россия",
        "iso_code_2": "RU",
        "iso_code_3": "RUS",
        "iso_numeric": "643",
        "is_active": True,
    },
    response_only=True,
    status_codes=["200"],
)

COUNTRY_LIST_EXAMPLE = OpenApiExample(
    name="Список стран (200)",
    description="Ответ с пагинацией",
    value={
        "count": 195,
        "next": "http://localhost:8000/api/addresses/countries/?page=2",
        "previous": None,
        "results": [
            {
                "id": "...",
                "name": "Россия",
                "iso_code_2": "RU",
                "iso_code_3": "RUS",
                "iso_numeric": "643",
                "is_active": True,
            },
            {
                "id": "...",
                "name": "США",
                "iso_code_2": "US",
                "iso_code_3": "USA",
                "iso_numeric": "840",
                "is_active": True,
            },
        ],
    },
    response_only=True,
    status_codes=["200"],
)

COUNTRY_LIST_NO_PAGINATION_EXAMPLE = OpenApiExample(
    name="Список стран без пагинации (200)",
    description="Ответ когда ?page= не указан — все записи",
    value={
        "count": 195,
        "results": [
            {"id": "...", "name": "Россия", "iso_code_2": "RU", "is_active": True},
            {"id": "...", "name": "США", "iso_code_2": "US", "is_active": True},
        ],
    },
    response_only=True,
    status_codes=["200"],
)

ADMIN_DIVISION_EXAMPLE = OpenApiExample(
    name="Адм. единица (200)",
    value={
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Московская область",
        "abbreviated_name": "МО",
        "code": "50",
        "level": {"id": "...", "name": "Регион", "level": 2, "show_in_address": True},
        "is_active": True,
    },
    response_only=True,
    status_codes=["200"],
)

LOCALITY_EXAMPLE = OpenApiExample(
    name="Населённый пункт (200)",
    value={
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "name": "Москва",
        "postal_code": "101000",
        "locality_type": {
            "id": "...",
            "name": "город",
            "abbreviated_name": "г.",
            "show_before_name": True,
            "has_administrative_division": True,
        },
        "administrative_division": {"id": "...", "name": "Московская область"},
        "is_active": True,
    },
    response_only=True,
    status_codes=["200"],
)

STREET_EXAMPLE = OpenApiExample(
    name="Улица (200)",
    value={
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "name": "Ленина",
        "locality": {"id": "...", "name": "Москва"},
        "street_type": {
            "id": "...",
            "name": "улица",
            "abbreviated_name": "ул.",
            "show_before_name": True,
        },
        "is_active": True,
    },
    response_only=True,
    status_codes=["200"],
)

HOUSE_EXAMPLE = OpenApiExample(
    name="Дом (200)",
    value={
        "id": "550e8400-e29b-41d4-a716-446655440005",
        "number": "1",
        "street": {"id": "...", "name": "Ленина"},
        "is_active": True,
    },
    response_only=True,
    status_codes=["200"],
)

BUILDING_EXAMPLE = OpenApiExample(
    name="Строение (200)",
    value={
        "id": "550e8400-e29b-41d4-a716-446655440006",
        "number": "А",
        "house": {"id": "...", "number": "1"},
        "is_active": True,
    },
    response_only=True,
    status_codes=["200"],
)

ADDRESS_FULL = OpenApiExample(
    name="Полный адрес (200)",
    description="Адрес со всеми заполненными компонентами",
    value={
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "country": {"id": "...", "name": "Россия", "iso_code_2": "RU"},
        "administrative_division": {"id": "...", "name": "Московская область"},
        "locality": {
            "id": "...",
            "name": "Москва",
            "locality_type": {"name": "город", "abbreviated_name": "г."},
        },
        "street": {
            "id": "...",
            "name": "Ленина",
            "street_type": {"name": "улица", "abbreviated_name": "ул."},
        },
        "house": {"id": "...", "number": "1"},
        "building": {"id": "...", "number": "А"},
        "coordinates": {"id": "...", "latitude": 55.755826, "longitude": 37.617300},
        "postal_code": "101000",
        "apartment": "15",
        "additional_info": "подъезд 2, этаж 3, домофон 15",
        "is_active": True,
        "full_address": "101000, Россия, Московская область, г. Москва, ул. Ленина, д. 1, стр. А, кв. 15",
        "created": "2026-06-20T08:00:00Z",
        "updated": "2026-06-25T10:00:00Z",
    },
    response_only=True,
    status_codes=["200"],
)

ADDRESS_MINIMAL = OpenApiExample(
    name="Минимальный адрес (200)",
    description="Адрес только со страной (остальное не заполнено)",
    value={
        "id": "550e8400-...",
        "country": {"id": "...", "name": "Россия", "iso_code_2": "RU"},
        "administrative_division": None,
        "locality": None,
        "street": None,
        "house": None,
        "building": None,
        "coordinates": None,
        "postal_code": None,
        "apartment": None,
        "additional_info": None,
        "is_active": True,
        "full_address": "Россия",
        "created": "2026-06-25T08:00:00Z",
        "updated": "2026-06-25T08:00:00Z",
    },
    response_only=True,
    status_codes=["200"],
)

ADDRESS_CREATED = OpenApiExample(
    name="Адрес создан (201)",
    description="Ответ при успешном создании адреса",
    value={
        "id": "550e8400-...",
        "country": {"name": "Россия", "iso_code_2": "RU"},
        "locality": {"name": "Москва"},
        "full_address": "Россия, г. Москва",
        "is_active": True,
        "created": "2026-06-25T10:00:00Z",
        "updated": "2026-06-25T10:00:00Z",
    },
    response_only=True,
    status_codes=["201"],
)

SEARCH_RESPONSE = OpenApiExample(
    name="Результат поиска (200)",
    value={
        "total": 5,
        "limit": 10,
        "offset": 0,
        "results": [
            {
                "id": "...",
                "country": {"name": "Россия"},
                "locality": {"name": "Москва"},
                "street": {"name": "Ленина"},
                "house": {"number": "1"},
                "full_address": "Россия, г. Москва, ул. Ленина, д. 1",
                "postal_code": "101000",
                "is_active": True,
            }
        ],
    },
    response_only=True,
    status_codes=["200"],
)

BULK_RESPONSE_ALL_OK = OpenApiExample(
    name="Массовое создание — всё успешно (201)",
    value={
        "created": [
            {"index": 0, "id": "uuid-1", "address": "Россия, г. Москва"},
            {"index": 1, "id": "uuid-2", "address": "Россия, г. Санкт-Петербург"},
        ],
        "errors": [],
        "total": 2,
        "success_count": 2,
        "error_count": 0,
    },
    response_only=True,
    status_codes=["201"],
)

BULK_RESPONSE_PARTIAL = OpenApiExample(
    name="Массовое создание — часть с ошибками (201)",
    description="Первый адрес создан, второй — ошибка валидации",
    value={
        "created": [{"index": 0, "id": "uuid-1", "address": "Россия, г. Москва"}],
        "errors": [{"index": 1, "errors": {"country": ["Обязательное поле."]}}],
        "total": 2,
        "success_count": 1,
        "error_count": 1,
    },
    response_only=True,
    status_codes=["201"],
)

BULK_RESPONSE_ALL_ERRORS = OpenApiExample(
    name="Массовое создание — всё с ошибками (400)",
    description="Ни один адрес не создан",
    value={
        "created": [],
        "errors": [
            {"index": 0, "errors": {"country": ["Обязательное поле."]}},
            {"index": 1, "errors": {"country": ["Обязательное поле."]}},
        ],
        "total": 2,
        "success_count": 0,
        "error_count": 2,
    },
    response_only=True,
    status_codes=["400"],
)


# --- Ошибки ---

ERROR_400_VALIDATION = OpenApiExample(
    name="Ошибка валидации (400)",
    description="Ответ когда данные не прошли проверку",
    value={
        "country": ["Обязательное поле."],
        "locality": ["Нельзя указать населённый пункт без страны."],
    },
    response_only=True,
    status_codes=["400"],
)

ERROR_400_SEARCH_EMPTY = OpenApiExample(
    name="Ошибка поиска — нет параметров (400)",
    description="Ответ когда ни один параметр поиска не указан",
    value={
        "non_field_errors": [
            'Укажите хотя бы один параметр для поиска. Например: {"query": "Москва"}'
        ]
    },
    response_only=True,
    status_codes=["400"],
)

ERROR_400_NOT_LIST = OpenApiExample(
    name="Ошибка массового создания — не массив (400)",
    description="Ответ когда в bulk_create передан не массив",
    value={"error": "Ожидается список адресов в формате JSON-массива"},
    response_only=True,
    status_codes=["400"],
)

ERROR_401 = OpenApiExample(
    name="Не авторизован (401)",
    description="Ответ при отсутствии или неверном JWT токене",
    value={"detail": "Учетные данные не были предоставлены."},
    response_only=True,
    status_codes=["401"],
)

ERROR_403 = OpenApiExample(
    name="Доступ запрещён (403)",
    description="Ответ когда прав недостаточно",
    value={"detail": "У вас недостаточно прав для выполнения данного действия."},
    response_only=True,
    status_codes=["403"],
)

ERROR_404 = OpenApiExample(
    name="Не найдено (404)",
    description="Ответ когда объект с указанным ID не существует",
    value={"detail": "Страница не найдена."},
    response_only=True,
    status_codes=["404"],
)


# --- Запросы ---

COUNTRY_CREATE_REQUEST = OpenApiExample(
    name="Создание страны (запрос)",
    value={
        "name": "Россия",
        "iso_code_2": "RU",
        "iso_code_3": "RUS",
        "iso_numeric": "643",
    },
    request_only=True,
)

ADDRESS_CREATE_NESTED_REQUEST = OpenApiExample(
    name="Создание адреса — вложенные объекты",
    description="Сервер сам создаст/найдет компоненты",
    value={
        "country": {"name": "Россия", "iso_code_2": "RU"},
        "locality": {"name": "Москва"},
        "street": {"name": "Ленина"},
        "house": {"number": "1"},
        "postal_code": "101000",
        "apartment": "15",
    },
    request_only=True,
)

ADDRESS_CREATE_BY_ID_REQUEST = OpenApiExample(
    name="Создание адреса — по ID",
    description="Все компоненты должны уже существовать в базе",
    value={
        "country_id": "550e8400-e29b-41d4-a716-446655440001",
        "locality_id": "550e8400-e29b-41d4-a716-446655440003",
        "street_id": "550e8400-e29b-41d4-a716-446655440004",
        "house_id": "550e8400-e29b-41d4-a716-446655440005",
        "postal_code": "101000",
    },
    request_only=True,
)

ADDRESS_CREATE_COUNTRY_ONLY_REQUEST = OpenApiExample(
    name="Создание адреса — только страна",
    description="Минимально возможный адрес",
    value={"country": {"name": "Россия", "iso_code_2": "RU"}},
    request_only=True,
)

SEARCH_REQUEST_EXAMPLE = OpenApiExample(
    name="Поиск адресов (запрос)",
    value={"query": "Москва Ленина 1", "limit": 10, "offset": 0},
    request_only=True,
)

BULK_REQUEST_EXAMPLE = OpenApiExample(
    name="Массовое создание (запрос)",
    value=[
        {
            "country": {"name": "Россия", "iso_code_2": "RU"},
            "locality": {"name": "Москва"},
        },
        {
            "country": {"name": "Россия", "iso_code_2": "RU"},
            "locality": {"name": "Санкт-Петербург"},
        },
    ],
    request_only=True,
)


# ══════════════════════════════════════════════════════════════════════════════════
# ДЕКОРАТОРЫ ДЛЯ ЭНДПОИНТОВ
# ══════════════════════════════════════════════════════════════════════════════════


def country_list_schema():
    """Схема для GET /api/addresses/countries/"""
    return extend_schema(
        summary="Получить список стран",
        description=(
            "Возвращает список всех стран.\n\n"
            "### Поиск\n"
            "Параметр `search` ищет по полям: `name`, `iso_code_2`, `iso_code_3`.\n"
            "Регистронезависимый. Можно искать часть слова.\n\n"
            "### Пагинация\n"
            "Без `?page=` — все страны сразу.\n"
            "С `?page=1` — по 100 на странице.\n"
            "`?limit=50` — изменить размер страницы.\n\n"
            "### Примеры URL\n"
            "- `/api/addresses/countries/` — все страны\n"
            "- `/api/addresses/countries/?search=Рос` — поиск\n"
            "- `/api/addresses/countries/?page=1&limit=20` — с пагинацией\n"
            "- `/api/addresses/countries/?ordering=-name` — сортировка"
        ),
        parameters=COMMON_PARAMETERS + PAGINATION_PARAMETERS,
        examples=[COUNTRY_LIST_EXAMPLE, COUNTRY_LIST_NO_PAGINATION_EXAMPLE],
    )


def country_create_schema():
    """Схема для POST /api/addresses/countries/"""
    return extend_schema(
        summary="Создать страну",
        description=(
            "Создание новой страны.\n\n"
            "### Обязательные поля\n"
            "- `name` — название страны\n"
            "- `iso_code_2` — двухбуквенный код (должен быть УНИКАЛЬНЫМ)\n\n"
            "### Необязательные поля\n"
            "- `iso_code_3` — трёхбуквенный код (уникальный)\n"
            "- `iso_numeric` — числовой код (уникальный)\n\n"
            "### Возможные ошибки\n"
            "- **400** — не указаны обязательные поля, или код уже занят\n"
            "- **401** — не авторизован (нужен JWT токен)"
        ),
        examples=[COUNTRY_CREATE_REQUEST, ERROR_400_VALIDATION, ERROR_401],
    )


def administrative_division_list_schema():
    """Схема для GET /api/addresses/administrative-divisions/"""
    return extend_schema(
        summary="Получить список административных единиц",
        description=(
            "Возвращает список административных единиц (области, районы, штаты).\n\n"
            "### Иерархия\n"
            "Единицы организованы в древовидную структуру:\n"
            "- Уровень 1 → Федеральный округ / Штат\n"
            "- Уровень 2 → Регион / Провинция\n"
            "- Уровень 3 → Район / Графство\n\n"
            "### Фильтры\n"
            "- `country` — все единицы страны\n"
            "- `level` — единицы конкретного уровня\n"
            "- `parent` — дочерние единицы (например: районы внутри области)"
        ),
        parameters=COMMON_PARAMETERS
        + PAGINATION_PARAMETERS
        + [
            OpenApiParameter(
                "country",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="ID страны",
            ),
            OpenApiParameter(
                "level",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="ID уровня",
            ),
            OpenApiParameter(
                "parent",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="ID родительской единицы",
            ),
        ],
        examples=[ADMIN_DIVISION_EXAMPLE],
    )


def locality_list_schema():
    """Схема для GET /api/addresses/localities/"""
    return extend_schema(
        summary="Получить список населённых пунктов",
        description=(
            "Возвращает список населённых пунктов (города, посёлки, деревни).\n\n"
            "### Типы\n"
            "У каждого пункта есть `locality_type`:\n"
            "- город (г.) — `show_before_name: true`\n"
            "- посёлок (п.)\n"
            "- деревня (д.)\n"
            "- село (с.)\n\n"
            "### Фильтры\n"
            "- `country` — нас. пункты страны\n"
            "- `administrative_division` — в конкретной области\n"
            "- `locality_type` — только города / только деревни\n"
            "- `postal_code` — по индексу"
        ),
        parameters=COMMON_PARAMETERS
        + PAGINATION_PARAMETERS
        + [
            OpenApiParameter(
                "country",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="ID страны",
            ),
            OpenApiParameter(
                "administrative_division",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="ID адм. единицы",
            ),
            OpenApiParameter(
                "locality_type",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="ID типа",
            ),
            OpenApiParameter(
                "postal_code",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Почтовый индекс",
            ),
        ],
        examples=[LOCALITY_EXAMPLE],
    )


def address_list_schema():
    """Схема для GET /api/addresses/addresses/"""
    return extend_schema(
        summary="Получить список адресов",
        description=(
            "Возвращает список адресов с возможностью поиска и фильтрации.\n\n"
            "### Поиск (`search`)\n"
            "Ищет по ВСЕМ компонентам адреса одновременно:\n"
            "страна, область, город, улица, дом, строение, индекс, квартира, доп. информация.\n\n"
            "**Как работает:**\n"
            "- Слова в запросе объединяются по И (все должны быть найдены)\n"
            "- Слова короче 2 букв игнорируются\n"
            "- Регистр не учитывается\n\n"
            "Пример: `?search=Москва Ленина 1` найдёт адреса где есть И Москва, И Ленина, И 1.\n\n"
            "### Фильтры\n"
            "- `country` — адреса в стране\n"
            "- `administrative_division` — в области\n"
            "- `locality` — в городе\n"
            "- `street` — на улице\n"
            "- `postal_code` — по индексу\n"
            "- `is_active` — активные (true) или неактивные (false)"
        ),
        parameters=COMMON_PARAMETERS
        + PAGINATION_PARAMETERS
        + [
            OpenApiParameter(
                "country",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="ID страны",
            ),
            OpenApiParameter(
                "administrative_division",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="ID адм. единицы",
            ),
            OpenApiParameter(
                "locality",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="ID нас. пункта",
            ),
            OpenApiParameter(
                "street",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="ID улицы",
            ),
            OpenApiParameter(
                "postal_code",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Почтовый индекс",
            ),
            OpenApiParameter(
                "is_active",
                OpenApiTypes.BOOL,
                OpenApiParameter.QUERY,
                description="Активность (true/false)",
            ),
        ],
        examples=[ADDRESS_FULL, ADDRESS_MINIMAL],
    )


def address_create_schema():
    """Схема для POST /api/addresses/addresses/"""
    return extend_schema(
        summary="Создать адрес",
        description=(
            "Создание нового адреса. Поддерживается два способа.\n\n"
            "### Способ 1: С вложенными объектами (рекомендуемый)\n"
            "Передаёте данные компонентов. Сервер сам создаст недостающие "
            "или найдёт существующие по уникальным полям.\n"
            "```json\n"
            "{\n"
            '  "country": {"name": "Россия", "iso_code_2": "RU"},\n'
            '  "locality": {"name": "Москва"},\n'
            '  "street": {"name": "Ленина"},\n'
            '  "house": {"number": "1"},\n'
            '  "postal_code": "101000"\n'
            "}\n"
            "```\n\n"
            "### Способ 2: По ID существующих объектов\n"
            "Быстрее, но ВСЕ компоненты должны уже существовать в базе.\n"
            "```json\n"
            "{\n"
            '  "country_id": "550e8400-...",\n'
            '  "locality_id": "550e8400-...",\n'
            '  "street_id": "550e8400-...",\n'
            '  "house_id": "550e8400-..."\n'
            "}\n"
            "```\n\n"
            "### Правила иерархии (проверки)\n"
            "- Строение → требует Дом\n"
            "- Дом → требует Улицу\n"
            "- Улица → требует Нас. пункт\n"
            "- Нас. пункт → требует Страну\n\n"
            "### Возможные ошибки\n"
            "- **400** — нарушена иерархия, неверный формат данных\n"
            "- **401** — не авторизован\n"
            "- **404** — указанный ID не найден (для способа 2)"
        ),
        examples=[
            ADDRESS_CREATE_NESTED_REQUEST,
            ADDRESS_CREATE_BY_ID_REQUEST,
            ADDRESS_CREATE_COUNTRY_ONLY_REQUEST,
            ADDRESS_CREATED,
            ERROR_400_VALIDATION,
            ERROR_401,
            ERROR_404,
        ],
    )


def address_search_schema():
    """Схема для POST /api/addresses/addresses/search/"""
    return extend_schema(
        summary="Поиск адресов (расширенный)",
        description=(
            "Расширенный поиск адресов через POST запрос.\n\n"
            "### Отличие от GET /addresses/\n"
            "Параметры передаются в теле запроса (JSON), а не в URL.\n"
            "Удобно для сложных поисковых запросов.\n\n"
            "### Параметры\n"
            "| Параметр | Тип | Описание |\n"
            "|----------|-----|----------|\n"
            "| query | string | Поисковый запрос |\n"
            "| country | UUID | ID страны |\n"
            "| administrative_division | UUID | ID области |\n"
            "| locality | UUID | ID города |\n"
            "| street | UUID | ID улицы |\n"
            "| postal_code | string | Индекс |\n"
            "| limit | integer | Сколько результатов (1-1000, по умолч. 100) |\n"
            "| offset | integer | Сколько пропустить (по умолч. 0) |\n\n"
            "**Хотя бы один параметр поиска обязателен!**\n\n"
            "### Примеры\n"
            "Простой поиск:\n"
            '{"query": "Москва Ленина", "limit": 10}\n\n'
            "С фильтром по стране:\n"
            '{"query": "Ленина", "country": "uuid-страны", "limit": 50}'
        ),
        examples=[SEARCH_REQUEST_EXAMPLE, SEARCH_RESPONSE, ERROR_400_SEARCH_EMPTY],
    )


def address_bulk_create_schema():
    """Схема для POST /api/addresses/addresses/bulk_create/"""
    return extend_schema(
        summary="Массовое создание адресов",
        description=(
            "Создание нескольких адресов за один запрос.\n\n"
            "### Как работает\n"
            "- Принимает JSON-массив адресов\n"
            "- Каждый адрес проверяется и сохраняется НЕЗАВИСИМО\n"
            "- Успешные → `created[]`\n"
            "- Ошибочные → `errors[]` с описанием что не так\n"
            "- Даже если часть с ошибками — успешные всё равно сохраняются\n\n"
            "### Формат ответа\n"
            "```json\n"
            "{\n"
            '  "created": [{"index": 0, "id": "uuid", "address": "Россия, г. Москва"}],\n'
            '  "errors": [{"index": 1, "errors": {"country": ["Обязательное поле."]}}],\n'
            '  "total": 2,\n'
            '  "success_count": 1,\n'
            '  "error_count": 1\n'
            "}\n"
            "```\n\n"
            "### Возможные ответы\n"
            "- **201** — все адреса созданы (или часть создана, часть с ошибками)\n"
            "- **400** — ни один не создан (все с ошибками, или передан не массив)\n"
            "- **401** — не авторизован"
        ),
        examples=[
            BULK_REQUEST_EXAMPLE,
            BULK_RESPONSE_ALL_OK,
            BULK_RESPONSE_PARTIAL,
            BULK_RESPONSE_ALL_ERRORS,
            ERROR_400_NOT_LIST,
            ERROR_401,
        ],
    )


def city_list_schema():
    """Схема для GET /api/addresses/cities/"""
    return extend_schema(
        summary="Получить список городов",
        description=(
            "Возвращает список городов с количеством номенклатур.\n\n"
            "### Поиск\n"
            "Параметр `search` ищет по названию города, региона или федерального округа.\n\n"
            "### Фильтры\n"
            "- `regions` — фильтр по регионам (UUID через запятую)\n"
            "- `federal_districts` — фильтр по федеральным округам (UUID через запятую)\n\n"
            "### Пагинация\n"
            "Без `?page=` — все города сразу.\n"
            "С `?page=1` — по 100 на странице.\n"
        ),
        parameters=COMMON_PARAMETERS + PAGINATION_PARAMETERS,
    )


def street_list_schema():
    """Схема для GET /api/addresses/streets/"""
    return extend_schema(
        summary="Получить список улиц",
        description=(
            "Возвращает список улиц.\n\n"
            "### Поиск\n"
            "Параметр `search` ищет по названию улицы или города.\n\n"
            "### Фильтры\n"
            "- `cities` — фильтр по городам (UUID через запятую)\n\n"
            "### Пагинация\n"
            "Без `?page=` — все улицы сразу.\n"
            "С `?page=1` — по 100 на странице.\n"
        ),
        parameters=COMMON_PARAMETERS + PAGINATION_PARAMETERS,
    )
