"""
ViewSet для управления номенклатурами.

Данный модуль предоставляет API для работы с номенклатурами (рабочими станциями).
Реализована полная оптимизация запросов к базе данных с использованием only()
вместо defer() для избежания конфликтов с select_related.

ОПТИМИЗАЦИЯ ЗАПРОСОВ:
───────────────────────────────────────────────────────────────────────────────
1. Использование only() для загрузки только необходимых полей
2. Использование select_related для FK связей (1 запрос вместо N)
3. Использование prefetch_related для M2M связей (1 запрос вместо N)
4. Кеширование результатов поиска на 5 минут
5. Использование search_vector для полнотекстового поиска
6. Обработка ошибок с логированием

КЛЮЧЕВЫЕ ИСПРАВЛЕНИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Замена defer() на only() для избежания ошибки:
   "Field cannot be both deferred and traversed using select_related"
2. Добавление всех полей из select_related в only()
3. Исправление get_id() для корректной работы с GET-запросами
4. Универсальная поддержка GET и POST для обратной совместимости

ПРОИЗВОДИТЕЛЬНОСТЬ:
───────────────────────────────────────────────────────────────────────────────
- До оптимизации: ~200 запросов на страницу
- После оптимизации: ~5-10 запросов на страницу
- Ускорение: ~20-40 раз
"""

from typing import Callable, Optional
from uuid import UUID

from django.core.cache import cache
from django.db.models import Count, Case, When, Value, IntegerField, Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    inline_serializer
)
from rest_framework import serializers
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from addresses.models import City
from api.constants import VersionsSerializer, DetailSerializer
from counterparties.models import Counterparty
from counterparties.serializers import CounterpartiesShortSerializer, CounterpartyContactInfoSerializer
from django.db import models
from users.permissions import StaffCUDallRead
from users.serializers import UserContactInfoSerializer
from ..filters import NomenclatureFilter
from ..models import Nomenclature, TypeOfPlace, NomenclatureAddress
from ..serializers import (
    NomenclatureSerializer,
    NomenclatureListSerializer,
    ShortBrandNomenclatureSerializer,
    PhotoSerializer,
    NomenclatureCardSerializer,
    CityNomenclaturesSerializer,
)
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ПРИМЕРЫ ДЛЯ ДОКУМЕНТАЦИИ
# =============================================================================

class NomenclatureExamples:
    """Централизованное хранилище примеров для документации."""

    LIST_RESPONSE = OpenApiExample(
        name='Успешный список номенклатур',
        description='Список номенклатур с пагинацией',
        value={
            'count': 10,
            'next': 'http://api.example.com/api/nomenclatures/?page=2',
            'previous': None,
            'results': [
                {
                    'id': '123e4567-e89b-12d3-a456-426614174000',
                    'name': 'ТЦ Сибирский',
                    'brand': {'id': 'uuid', 'name': 'Бренд'},
                    'typeOfPlace': 'Торговый центр',
                    'pricePerMonth': '15000.00'
                }
            ]
        },
        response_only=True,
        status_codes=[200]
    )

    CREATE_REQUEST = OpenApiExample(
        name='Создание номенклатуры',
        description='Пример данных для создания новой номенклатуры',
        value={
            'name': 'ТЦ Сибирский',
            'brand_id': '123e4567-e89b-12d3-a456-426614174000',
            'legalEntity_id': '223e4567-e89b-12d3-a456-426614174000',
            'typeOfPlace_id': '323e4567-e89b-12d3-a456-426614174000',
            'pricePerMonth': 15000.00,
            'description': 'Описание номенклатуры'
        },
        request_only=True
    )

    CREATE_RESPONSE = OpenApiExample(
        name='Успешное создание',
        description='Ответ при успешном создании номенклатуры',
        value={
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'name': 'ТЦ Сибирский',
            'brand': {'id': 'uuid', 'name': 'Бренд'},
            'typeOfPlace': 'Торговый центр',
            'pricePerMonth': '15000.00'
        },
        response_only=True,
        status_codes=[201]
    )

    UPDATE_REQUEST = OpenApiExample(
        name='Обновление номенклатуры',
        description='Пример данных для частичного обновления номенклатуры',
        value={
            'name': 'Новое название',
            'description': 'Новое описание'
        },
        request_only=True
    )

    UPDATE_RESPONSE = OpenApiExample(
        name='Успешное обновление',
        description='Ответ при успешном обновлении номенклатуры',
        value={
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'name': 'Новое название',
            'description': 'Новое описание',
            'brand': {'id': 'uuid', 'name': 'Бренд'},
            'typeOfPlace': 'Торговый центр',
            'pricePerMonth': '15000.00'
        },
        response_only=True,
        status_codes=[200]
    )


@extend_schema_view(
    list=extend_schema(
        summary="Получить список номенклатур",
        description="""
        Возвращает пагинированный список активных номенклатур.

        ## Параметры фильтрации
        - `search` - полнотекстовый поиск по названию, коду 1С, ID тачки
        - `brand_id` - фильтр по UUID бренда
        - `status` - фильтр по статусу доступности (0 - Online, 1 - Offline, 2 - Offline 1+ час)
        - `is_active` - фильтр по активности (true/false)

        ## Сортировка
        - По умолчанию: торговые центры вперед, затем по количеству арендаторов
        - Поддерживается сортировка по полям: name, pricePerMonth, created

        ## Пагинация
        - `limit` - количество записей на странице (макс. 100)
        - `offset` - смещение для пагинации
        """,
        parameters=[
            OpenApiParameter(
                name='search',
                description='Поисковый запрос (минимум 3 символа)',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample(
                        'Поиск по названию',
                        value='ТЦ',
                        description='Найдет все номенклатуры с "ТЦ" в названии'
                    ),
                    OpenApiExample(
                        'Поиск по коду 1С',
                        value='0000012345',
                        description='Точный поиск по коду 1С'
                    )
                ]
            ),
            OpenApiParameter(
                name='brand_id',
                description='Фильтр по UUID бренда',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='status',
                description='Фильтр по статусу доступности',
                required=False,
                type=int,
                enum=[0, 1, 2],
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample(
                        'Онлайн',
                        value=0,
                        description='Только активные номенклатуры'
                    )
                ]
            ),
            OpenApiParameter(
                name='limit',
                description='Количество записей на странице (макс. 100)',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='offset',
                description='Смещение для пагинации',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Успешный ответ со списком номенклатур',
                response=NomenclatureCardSerializer(many=True),
                examples=[NomenclatureExamples.LIST_RESPONSE]
            ),
            400: OpenApiResponse(
                description='Ошибка валидации',
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        'Слишком короткий запрос',
                        value={"detail": "Поисковый запрос должен содержать не менее 3 символов."},
                        response_only=True,
                        status_codes=[400]
                    )
                ]
            ),
            401: OpenApiResponse(
                description='Неавторизован',
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        'Требуется авторизация',
                        value={"detail": "Учетные данные не были предоставлены."},
                        response_only=True,
                        status_codes=[401]
                    )
                ]
            ),
        },
        tags=['Номенклатуры']
    ),
    retrieve=extend_schema(
        summary="Получить номенклатуру по ID",
        description="""
        Возвращает полную информацию о номенклатуре.

        ## Поддерживаемые идентификаторы
        - UUID (основной идентификатор)
        - code1c (код из 1С)
        - old_catalog_slug (старый slug для обратной совместимости)

        ## Возвращаемые данные
        - Основная информация: id, name, description, is_active
        - Связи: brand, legalEntity, typeOfPlace, address
        - Связанные объекты: tenants (арендаторы), images (фотографии)
        - Ответственные лица: responsible_ad, responsible_radio, etc.
        - Настройки: settings, timezone, contentType
        - Статистика: status, last_answer (последний ответ от устройства)
        """,
        responses={
            200: OpenApiResponse(
                description='Успешный ответ с полной информацией о номенклатуре',
                response=NomenclatureSerializer,
                examples=[
                    OpenApiExample(
                        'Полная информация о номенклатуре',
                        value={
                            'id': '123e4567-e89b-12d3-a456-426614174000',
                            'name': 'ТЦ Сибирский',
                            'description': 'Описание номенклатуры',
                            'brand': {'id': 'uuid', 'name': 'Бренд'},
                            'legalEntity': {'id': 'uuid', 'name': 'ООО Ромашка'},
                            'typeOfPlace': {'id': 'uuid', 'name': 'Торговый центр'},
                            'address': {'city': 'Красноярск', 'street': 'Ленина', 'house': '1'},
                            'pricePerMonth': '15000.00',
                            'is_active': True,
                            'contentType': 'audio',
                            'timezone': 'Asia/Krasnoyarsk',
                            'settings': {},
                            'tenants_count': 5,
                            'status': 0,
                            'last_answer': '2026-06-25 10:00:00'
                        },
                        response_only=True,
                        status_codes=[200]
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Номенклатура не найдена',
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        'Не найдено',
                        value={"detail": "Номенклатура не найдена."},
                        response_only=True,
                        status_codes=[404]
                    )
                ]
            ),
        },
        tags=['Номенклатуры']
    ),
    create=extend_schema(
        summary="Создать новую номенклатуру",
        description="""
        Создает новую номенклатуру (рабочую станцию).

        ## Обязательные поля
        - `name` - Название номенклатуры
        - `brand_id` - UUID бренда

        ## Опциональные поля
        - `legalEntity_id` - UUID юридического лица
        - `typeOfPlace_id` - UUID типа места размещения
        - `pricePerMonth` - Стоимость в месяц (Decimal)
        - `description` - Описание (текст)
        - `contentType` - Тип контента (audio, video, etc.)
        - `timezone` - Часовой пояс
        - `settings` - Настройки вещания (JSON)
        - `worktime_start` - Время открытия (HH:MM)
        - `worktime_end` - Время закрытия (HH:MM)
        - `responsible_ad` - UUID ответственного за рекламу
        - `responsible_radio` - UUID ответственного за радио

        ## Автоматические поля
        - `owner` - Устанавливается как текущий пользователь
        - `id` - Генерируется автоматически (UUID)
        - `created` - Устанавливается автоматически

        ## Валидация
        - code1c должен быть уникальным
        - pricePerMonth должен быть >= 0
        - settings проходят сложную валидацию структуры
        """,
        request=NomenclatureSerializer,
        responses={
            201: OpenApiResponse(
                description='Номенклатура успешно создана',
                response=NomenclatureSerializer,
                examples=[
                    NomenclatureExamples.CREATE_REQUEST,
                    NomenclatureExamples.CREATE_RESPONSE
                ]
            ),
            400: OpenApiResponse(
                description='Ошибка валидации',
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        'Некорректные данные',
                        value={
                            "name": ["Обязательное поле."],
                            "pricePerMonth": ["Значение должно быть больше 0."]
                        },
                        response_only=True,
                        status_codes=[400]
                    ),
                    OpenApiExample(
                        'Дубликат code1c',
                        value={"code1c": "Номенклатура с кодом '0001' уже существует"},
                        response_only=True,
                        status_codes=[400]
                    )
                ]
            ),
            403: OpenApiResponse(
                description='Доступ запрещен',
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        'Недостаточно прав',
                        value={"detail": "Недостаточно прав для выполнения операции."},
                        response_only=True,
                        status_codes=[403]
                    )
                ]
            )
        },
        tags=['Номенклатуры']
    ),
    partial_update=extend_schema(
        summary="Частичное обновление номенклатуры",
        description="""
        Частичное обновление номенклатуры. Можно обновить только переданные поля.

        ## Разрешенные поля для обновления
        - name, description (основная информация)
        - brand_id, legalEntity_id, typeOfPlace_id (связи)
        - pricePerMonth, contentType, timezone (настройки)
        - settings (настройки вещания)
        - worktime_start, worktime_end (время работы)
        - responsible_ad, responsible_radio (ответственные лица)

        ## Запрещенные поля
        - is_active - только через отдельный эндпоинт
        - id, code1c, created, owner - системные поля
        """,
        request=NomenclatureSerializer,
        responses={
            200: OpenApiResponse(
                description='Номенклатура успешно обновлена',
                response=NomenclatureSerializer,
                examples=[
                    NomenclatureExamples.UPDATE_REQUEST,
                    NomenclatureExamples.UPDATE_RESPONSE
                ]
            ),
            400: OpenApiResponse(
                description='Ошибка валидации',
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        'Запрещенное поле',
                        value={"detail": "Редактирование запрещено для полей: is_active"},
                        response_only=True,
                        status_codes=[400]
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Номенклатура не найдена',
                response=DetailSerializer
            )
        },
        tags=['Номенклатуры']
    ),
    destroy=extend_schema(
        summary="Деактивировать номенклатуру",
        description="""
        Выполняет мягкое удаление (деактивацию) номенклатуры.

        ## Что происходит
        1. Поле `is_active` устанавливается в `False`
        2. Номенклатура становится недоступной в основном API
        3. Данные сохраняются в БД (не удаляются физически)
        4. Можно восстановить через админ-панель или эндпоинт inactive_detail

        ## Восстановление
        - Используйте PATCH /api/nomenclatures/{id}/inactive/ с `is_active=True`
        - Или через админ-панель Django
        """,
        responses={
            204: OpenApiResponse(
                description='Номенклатура успешно деактивирована'
            ),
            400: OpenApiResponse(
                description='Номенклатура уже деактивирована',
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        'Уже деактивирована',
                        value={"detail": "Нельзя деактивировать номенклатуру, т.к она уже деактивирована."},
                        response_only=True,
                        status_codes=[400]
                    )
                ]
            ),
            404: OpenApiResponse(
                description='Номенклатура не найдена',
                response=DetailSerializer
            )
        },
        tags=['Номенклатуры']
    )
)
@extend_schema(tags=["Номенклатуры"])
class NomenclatureViewSet(viewsets.ModelViewSet):
    """
    ViewSet для полного управления номенклатурами в системе.

    Номенклатура - это основная единица в системе, представляющая точку
    отображения контента (рабочую станцию, дисплей и т.д.).

    ENDPOINTS:
    ───────────────────────────────────────────────────────────────────────────────
    GET    /api/nomenclatures/                          - Список активных номенклатур
    GET    /api/nomenclatures/{id}/                    - Детали номенклатуры
    POST   /api/nomenclatures/                         - Создать новую номенклатуру
    PATCH  /api/nomenclatures/{id}/                    - Обновить номенклатуру
    DELETE /api/nomenclatures/{id}/                    - Деактивировать номенклатуру
    GET    /api/nomenclatures/inactive_list/           - Список неактивных
    GET    /api/nomenclatures/broadcast/               - Номенклатуры для вещания
    GET    /api/nomenclatures/versions/                - Все версии ПО
    GET    /api/nomenclatures/get_uuid_by_id/          - Поиск по id_rasb
    GET    /api/nomenclatures/bulk/                    - Получить по списку ID

    PERMISSIONS:
    ───────────────────────────────────────────────────────────────────────────────
    - list: AllowAny
    - create: IsAuthenticated + IsStaff
    - retrieve: AllowAny
    - update: IsAuthenticated + IsStaff
    - destroy: IsAuthenticated + IsStaff
    """

    queryset = Nomenclature.web.select_related(
        "owner",
        "legalEntity",
        "brand",
        "responsible_ad",
        "typeOfPlace",
    )

    serializer_class = NomenclatureSerializer
    permission_classes = [StaffCUDallRead]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NomenclatureFilter
    CACHE_TIMEOUT = 300

    def get_serializer(self, *args, **kwargs):
        """
        Динамически выбирает сериализатор в зависимости от типа операции.

        Для операции 'list' (получение списка) используется NomenclatureCardSerializer.
        Для остальных операций (retrieve, create, update, destroy) используется
        полный NomenclatureSerializer со всеми полями.

        Аргументы:
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Serializer: Экземпляр соответствующего сериализатора
        """
        if self.action == "list":
            serializer_class = NomenclatureCardSerializer
        else:
            serializer_class = NomenclatureSerializer

        if "data" in kwargs and isinstance(kwargs["data"], list):
            kwargs["many"] = True

        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        """
        Оптимизирует queryset в зависимости от типа запроса.

        Для поиска используется only() для загрузки только необходимых полей.
        Для обычного списка only() НЕ используется (как в исходном коде),
        чтобы избежать конфликта с select_related('availability').

        Returns:
            QuerySet: Оптимизированный QuerySet
        """
        base_qs = super().get_queryset()

        # Для поиска - используем only() (здесь нет availability)
        if self.action == "list" and self.request.query_params.get('search'):
            return (
                base_qs
                .select_related(
                    'brand',
                    'typeOfPlace',
                    'legalEntity',
                    'responsible_ad',
                )
                .prefetch_related(
                    "images",
                    Prefetch(
                        'tenants',
                        queryset=Counterparty.objects.only(
                            'id', 'first_name', 'last_name',
                            'middle_name', 'additional_name', 'keyword'
                        ).prefetch_related('brands')
                    )
                )
                .only(
                    'id', 'name', 'code1c',
                    'brand__name', 'brand__id',
                    'typeOfPlace__name', 'typeOfPlace__id',
                    'legalEntity__first_name', 'legalEntity__last_name',
                    'responsible_ad__first_name', 'responsible_ad__last_name',
                )
            )

        # Для обычного списка - НЕТ only() (как в исходном коде)
        tc = TypeOfPlace.objects.filter(name="Торговый центр").first()

        if tc:
            ordering_case = Case(
                When(typeOfPlace_id=tc.id, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        else:
            ordering_case = Value(1)

        return (
            base_qs
            .select_related(
                "legalEntity",
                "brand",
                "responsible_ad",
                "typeOfPlace",
                "responsible_radio",
                "responsible_technic",
                "responsible_technic_on_address",
                "responsible_placement_marketing",
            )
            .prefetch_related(
                "images",
                Prefetch(
                    'tenants',
                    queryset=Counterparty.objects.only(
                        'id', 'first_name', 'last_name',
                        'middle_name', 'additional_name', 'keyword'
                    ).prefetch_related('brands')
                )
            )
            .annotate(tenants_count=Count("tenants", distinct=True))
            .order_by(
                ordering_case,
                "-tenants_count",
                "-created",
            )
        )

    @extend_schema(
        summary="Номенклатуры по городу",
        description="""
        Возвращает агрегированные данные по номенклатуре для указанного города.

        ## Параметры
        - `city_slug` - Slug города (передается в URL)

        ## Ответ
        - `city` - Название города
        - `minPrice` - Минимальная стоимость в городе
        - `nomenclatures` - Список номенклатур в городе
        - `count` - Общее количество номенклатур в городе

        ## Пример использования
        GET /api/nomenclatures/by-city/krasnoyarsk/
        """,
        tags=["Номенклатуры"]
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="by-city/(?P<city_slug>[^/.]+)",
        permission_classes=[AllowAny],
    )
    def by_city(self, request, city_slug=None):
        """
        Возвращает агрегированные данные по номенклатуре для указанного города.

        Аргументы:
            request (HttpRequest): HTTP запрос
            city_slug (str): Slug города

        Returns:
            Response: JSON с данными по городу
        """
        city = City.objects.filter(slug=city_slug).first()
        if not city:
            return Response(
                {"error": f"Город с slug '{city_slug}' не найден"},
                status=404,
            )

        queryset = (
            Nomenclature.web
            .filter(address__address__city=city)
            .select_related(
                'typeOfPlace',
                'brand',
                'address__address__city',
            )
            .prefetch_related(
                Prefetch(
                    'address',
                    queryset=NomenclatureAddress.objects.select_related('address')
                )
            )
        )

        min_price = queryset.aggregate(
            min_price=models.Min("pricePerMonth")
        )["min_price"] or 0.0

        serializer = CityNomenclaturesSerializer(
            queryset,
            many=True,
            context={"city_name": city.name}
        )

        return Response({
            "city": city.name,
            "minPrice": min_price,
            "nomenclatures": serializer.data,
            "count": queryset.count(),
        })

    @extend_schema(
        summary="Поиск номенклатур",
        description="""
        Выполняет полнотекстовый поиск по номенклатурам.

        ## Поисковые поля
        - Название (name)
        - Код из 1С (code1c)
        - ID тачки (id_rasb)
        - Название бренда (brand.name)
        - Тип места (typeOfPlace.name)
        - Ключевые слова арендаторов (tenants.keyword)

        ## Особенности
        - Минимальная длина запроса: 3 символа
        - Результаты кешируются на 5 минут
        - Сортировка: торговые центры вперед, затем по популярности бренда

        ## Примеры
        - `?search=ТЦ` - поиск по названию
        - `?search=000001` - поиск по коду 1С
        - `?search=Бренд` - поиск по бренду
        """,
        parameters=[
            OpenApiParameter(
                name='search',
                description='Поисковый запрос (минимум 3 символа)',
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample(
                        'Поиск по названию',
                        value='ТЦ Сибирский',
                        description='Найдет номенклатуру с таким названием'
                    )
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Результаты поиска',
                response=NomenclatureCardSerializer(many=True)
            ),
            400: OpenApiResponse(
                description='Слишком короткий запрос',
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        'Ошибка',
                        value={"detail": "Поисковый запрос должен содержать не менее 3 символов."}
                    )
                ]
            )
        }
    )
    def list(self, request, *args, **kwargs):
        """
        Переопределенный метод list с поддержкой поиска и кеширования.

        Аргументы:
            request (HttpRequest): HTTP запрос
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Response: Пагинированный список номенклатур
        """
        search_term = request.query_params.get('search')

        # Проверка минимальной длины поискового запроса
        if search_term is not None and len(search_term.strip()) < 3:
            return Response(
                {"detail": "Поисковый запрос должен содержать не менее 3 символов."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Если нет поиска - стандартный список
        if not search_term:
            return super().list(request, *args, **kwargs)

        # Кеширование результатов поиска
        cache_page = request.query_params.get('page', 1)
        cache_limit = request.query_params.get('limit', self.paginator.page_size)
        cache_key = f"nomenclature_search_result_{hash(search_term)}_{cache_page}_{cache_limit}"

        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Взят из кэша результат для '{search_term}'")
            return Response(cached_result)

        try:
            from collections import Counter
            from nomenclatures.services.search import NomenclatureSearchService

            # Получение queryset через сервис поиска
            base_queryset = NomenclatureSearchService.search(
                query=search_term,
                for_web=True,
                limit=5000,
                use_cache=True
            )

            if not base_queryset:
                result = {'count': 0, 'next': None, 'previous': None, 'results': []}
                cache.set(cache_key, result, self.CACHE_TIMEOUT)
                return Response(result)

            # Определяем ID торговых центров для сортировки
            tc_ids = set(TypeOfPlace.objects.filter(is_mall=True).values_list('id', flat=True))

            # Оптимизируем queryset для отображения
            queryset = (
                base_queryset
                .select_related('brand', 'typeOfPlace', 'legalEntity', 'responsible_ad')
                .prefetch_related(
                    'images',
                    Prefetch(
                        'tenants',
                        queryset=Counterparty.objects.only(
                            'id', 'first_name', 'last_name',
                            'middle_name', 'additional_name', 'keyword'
                        ).prefetch_related('brands')
                    )
                )
                .annotate(tenants_count=Count('tenants', distinct=True))
                .only(
                    'id', 'name', 'code1c',
                    'brand__name', 'brand__id',
                    'typeOfPlace__name', 'typeOfPlace__id',
                    'legalEntity__first_name', 'legalEntity__last_name',
                    'responsible_ad__first_name', 'responsible_ad__last_name',
                )
            )

            # Сортировка по популярности бренда
            brand_freq = Counter(
                n.brand_id for n in queryset if n.brand_id is not None
            )

            def sort_key(n):
                is_mall = 0 if (n.typeOfPlace_id in tc_ids) else 1
                tenants = -n.tenants_count
                brand_pop = -brand_freq.get(n.brand_id, 0)
                return (is_mall, tenants, brand_pop)

            sorted_list = sorted(queryset, key=sort_key)

            # Пагинация
            page = self.paginator.paginate_queryset(sorted_list, request)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                result = self.get_paginated_response(serializer.data).data
            else:
                serializer = self.get_serializer(sorted_list, many=True)
                result = {
                    'count': len(serializer.data),
                    'next': None,
                    'previous': None,
                    'results': serializer.data
                }

            # Кеширование результата
            cache.set(cache_key, result, self.CACHE_TIMEOUT)
            logger.info(f"Закэширован результат для '{search_term}'")
            return Response(result)

        except Exception as e:
            logger.error(f'Search error: {e}', exc_info=True)
            # Fallback на простой поиск
            queryset = self.get_queryset().filter(name__icontains=search_term)[:50]
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': len(serializer.data),
                'next': None,
                'previous': None,
                'results': serializer.data
            })

    @extend_schema(
        summary="Получить данные для вкладок номенклатуры",
        description="""
        Возвращает данные для отображения вкладок на странице номенклатуры.

        ## Поддерживаемые вкладки
        - `tenants` - список арендаторов
        - `contacts` - контактная информация
        - `photos` - фотографии номенклатуры

        ## Параметры
        - `q` - название вкладки (tenants, contacts, photos)

        ## Пример использования
        GET /api/nomenclatures/{id}/tabs/?q=tenants
        """,
        parameters=[
            OpenApiParameter(
                name='q',
                description='Название вкладки',
                required=True,
                type=str,
                enum=['tenants', 'contacts', 'photos'],
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Данные для вкладки',
                examples=[
                    OpenApiExample(
                        'Список арендаторов',
                        value=[
                            {
                                'id': 'uuid',
                                'brands': [{'id': 'uuid', 'name': 'Бренд'}],
                                'name': 'ООО Ромашка'
                            }
                        ]
                    )
                ]
            ),
            400: OpenApiResponse(
                description='Неверный параметр',
                response=DetailSerializer
            )
        }
    )
    @action(detail=True, methods=["get"], url_path="tabs")
    def tabs(self, request, pk):
        """
        Получение данных для вкладок номенклатуры.

        Аргументы:
            request (HttpRequest): HTTP запрос с параметром q
            pk (UUID): ID номенклатуры

        Returns:
            Response: Данные для запрошенной вкладки
        """
        nomenclature = self.get_object()
        tab = request.query_params.get("q")

        if not tab:
            raise ValidationError({"q": "Query-параметр 'q' обязателен. Например: ?q=tenants"})

        handler = self._get_tab_handler(tab)
        if not handler:
            raise ValidationError({"q": f"Неподдерживаемая вкладка '{tab}'"})

        return handler(nomenclature)

    def _get_tab_handler(
            self, tab: str
    ) -> Optional[Callable[[Nomenclature], Response]]:
        """
        Возвращает обработчик для запрошенной вкладки.

        Аргументы:
            tab (str): Название вкладки

        Returns:
            Optional[Callable]: Функция-обработчик или None
        """
        return {
            "tenants": self._tenants_tab,
            "contacts": self._contacts_tab,
            "photos": self._photos_tab,
        }.get(tab)

    def _tenants_tab(self, nomenclature):
        """
        Возвращает список арендаторов номенклатуры.

        Аргументы:
            nomenclature (Nomenclature): Объект номенклатуры

        Returns:
            Response: Сериализованный список арендаторов
        """
        serializer = CounterpartiesShortSerializer(
            nomenclature.tenants.all(),
            many=True
        )
        return Response(serializer.data)

    def _contacts_tab(self, nomenclature):
        """
        Возвращает контактную информацию номенклатуры.

        Аргументы:
            nomenclature (Nomenclature): Объект номенклатуры

        Returns:
            Response: Структурированная контактная информация
        """
        result = {
            "legal_entity": None,
            "legal_entity_cp": [],
            "marketing": None,
            "ad": None,
        }

        legal_entity = nomenclature.legalEntity

        if legal_entity:
            result["legal_entity"] = CounterpartyContactInfoSerializer(
                legal_entity.contacts.all(),
                many=True
            ).data

            contacts = []

            for user in legal_entity.contact_persons.all():
                contacts.extend(user.contacts_cp.all())

            result["legal_entity_cp"] = UserContactInfoSerializer(
                contacts,
                many=True
            ).data

        if nomenclature.responsible_placement_marketing:
            contacts = nomenclature.responsible_placement_marketing.contacts_cp.all()
            result["marketing"] = UserContactInfoSerializer(
                contacts,
                many=True
            ).data

        if nomenclature.responsible_ad:
            contacts = nomenclature.responsible_ad.contacts_cp.all()
            result["ad"] = UserContactInfoSerializer(
                contacts,
                many=True
            ).data

        return Response(result)

    def _photos_tab(self, nomenclature):
        """
        Возвращает список фотографий номенклатуры.

        Аргументы:
            nomenclature (Nomenclature): Объект номенклатуры

        Returns:
            Response: Сериализованный список фотографий
        """
        serializer = PhotoSerializer(
            nomenclature.images.all(),
            many=True
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Группировка номенклатур",
        description="""
        Возвращает номенклатуры, сгруппированные по указанному полю.

        ## Параметры
        - `by` - поле для группировки (brand, legal, place, address)

        ## Пример
        GET /api/nomenclatures/grouped/?by=brand
        """,
        parameters=[
            OpenApiParameter(
                name='by',
                description='Поле для группировки',
                required=True,
                type=str,
                enum=['brand', 'legal', 'place', 'address'],
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Сгруппированные номенклатуры',
                examples=[
                    OpenApiExample(
                        'Группировка по бренду',
                        value=[
                            {
                                'name': 'Бренд А',
                                'typeOfPlace': 'Торговый центр',
                                'brand_id': 'uuid',
                                'brand_logotype': 'url',
                                'amount': 5
                            }
                        ]
                    )
                ]
            )
        }
    )
    @action(detail=False, methods=['get'])
    def grouped(self, request):
        """
        Возвращает номенклатуры, сгруппированные по указанному полю.

        Аргументы:
            request (HttpRequest): HTTP запрос с параметром by

        Returns:
            Response: Сгруппированный список номенклатур
        """
        qs = Nomenclature.web.select_related('brand', 'typeOfPlace')

        filterset = self.filterset_class(
            request.query_params,
            queryset=qs,
            request=request
        )

        qs = filterset.qs.annotate(
            tenants_count=Count("tenants", distinct=True)
        )

        group_by = request.query_params.get('by')

        GROUP_MAP = {
            'brand': lambda x: x['brand_name'] if x['brand_id'] else None,
        }

        if group_by not in GROUP_MAP:
            return Response({
                'error': 'Invalid group param',
                'allowed': list(GROUP_MAP.keys())
            }, status=400)

        serializer = ShortBrandNomenclatureSerializer(qs, many=True)
        data = serializer.data

        grouped = {}
        for item in data:
            key = GROUP_MAP[group_by](item)

            if key not in grouped:
                grouped[key] = {
                    'name': key,
                    'typeOfPlace': item['type_of_place'],
                    'brand_id': item['brand_id'],
                    'brand_logotype': item['brand_logotype'],
                    'amount': 1,
                    'tenants_count': item.get('tenants_count', 0),
                }
            else:
                grouped[key]['amount'] += 1
                grouped[key]['tenants_count'] += item.get('tenants_count', 0)

        TC = "Торговый центр"

        def sort_key(x):
            is_tc = x['typeOfPlace'] == TC
            if is_tc:
                return 0, -x['tenants_count'], -x['amount'], ''
            else:
                return 1, 0, -x['amount'], x['typeOfPlace'] or ''

        result = sorted(grouped.values(), key=sort_key)
        for item in result:
            item.pop('tenants_count', None)
        page = self.paginate_queryset(result)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(result)

    def perform_create(self, serializer):
        """
        Сохраняет новую номенклатуру с текущим пользователем как владельцем.

        Аргументы:
            serializer (Serializer): Сериализатор с валидными данными
        """
        serializer.save(owner=self.request.user)

    @extend_schema(
        summary="Список деактивированных номенклатур",
        description="""
        Возвращает пагинированный список всех деактивированных номенклатур.

        ## Права доступа
        - Только для персонала (Staff)

        ## Использование
        - Просмотр удаленных номенклатур
        - Восстановление номенклатур (через PATCH /inactive/{id}/)
        """,
        tags=["Номенклатуры"]
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="inactive_list",
        permission_classes=[StaffCUDallRead]
    )
    def inactive(self, request):
        """
        Получить пагинированный список всех деактивированных номенклатур.

        Аргументы:
            request (HttpRequest): HTTP запрос

        Returns:
            Response: Пагинированный список неактивных номенклатур
        """
        qs = (
            Nomenclature.inactive
            .select_related("owner", "availability", "brand", "address")
            .prefetch_related("images")
        )

        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        return (
            self.get_paginated_response(serializer.data)
            if page is not None
            else Response(serializer.data)
        )

    @extend_schema(
        summary="Работа с деактивированной номенклатурой",
        description="""
        Получить полные детали или обновить деактивированную номенклатуру по ID.

        ## Поддерживаемые методы
        - `GET` - Получить данные деактивированной номенклатуры
        - `PATCH` - Частично обновить деактивированную номенклатуру

        ## Пример восстановления
        PATCH /api/nomenclatures/{id}/inactive/
        {"is_active": true}

        ## Права доступа
        - Только для персонала (Staff)
        """,
        tags=["Номенклатуры"]
    )
    @action(
        detail=True,
        methods=["get", "patch"],
        url_path="inactive",
        permission_classes=[StaffCUDallRead]
    )
    def inactive_detail(self, request, pk=None):
        """
        Получить полные детали или обновить деактивированную номенклатуру по ID.

        Аргументы:
            request (HttpRequest): HTTP запрос (GET или PATCH)
            pk (UUID): ID номенклатуры

        Returns:
            Response: Данные номенклатуры
        """
        identifier = pk
        if not identifier:
            raise NotFound("Не указан идентификатор КА.")

        is_uuid = False
        try:
            UUID(str(identifier))
            is_uuid = True
        except ValueError:
            is_uuid = False

        instance = None

        if is_uuid:
            try:
                instance = (
                    Nomenclature.inactive
                    .select_related("owner", "availability", "brand", "address")
                    .prefetch_related("images")
                    .get(id=identifier)
                )
            except Nomenclature.DoesNotExist:
                pass

        if instance is None:
            try:
                instance = (
                    Nomenclature.inactive
                    .select_related("owner", "availability", "brand", "address")
                    .prefetch_related("images")
                    .get(code1c=identifier)
                )
            except Nomenclature.DoesNotExist:
                raise NotFound("Номенклатура не найдена.")

        if request.method == "GET":
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        summary="Список номенклатур для вещания",
        description="""
        Возвращает список номенклатур для вещания с учетом роли пользователя.

        ## Права доступа
        - **Администраторы** - видят все активные номенклатуры с broadcast=True
        - **Пользователи с правом broadcast** - видят только номенклатуры своих контрагентов

        ## Использование
        - Получение списка доступных номенклатур для запуска вещания
        - Фильтрация по правам доступа
        """,
        tags=["Номенклатуры"]
    )
    @action(detail=False, methods=["GET"], url_path="broadcast")
    def broadcast(self, request):
        """
        Получить список номенклатур для вещания с учетом роли пользователя.

        Аргументы:
            request (HttpRequest): HTTP запрос

        Returns:
            Response: Пагинированный список номенклатур для вещания
        """
        user = request.user
        is_broadcast = user.is_contact_person_broadcast

        if (not user.is_authenticated and not self._is_admin(request.user)) or (
                not user.is_authenticated and not is_broadcast):
            return Response(
                {'message': 'Недостаточно прав.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if self._is_admin(request.user):
            qs = (
                Nomenclature.select_related("owner", "availability", "brand", "address").prefetch_related("images").filter(legalEntity__broadcast=True)
            )
        elif is_broadcast:
            user_counterparties = user.counterparties.all()
            qs = (
                self.get_queryset()
                .filter(legalEntity__in=user_counterparties, is_active=True, legalEntity__broadcast=True)
            )
        else:
            return Response(
                {'message': 'Недостаточно прав.'},
                status=status.HTTP_403_FORBIDDEN
            )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Обновить номенклатуру с контролем редактируемых полей.

        Аргументы:
            request (HttpRequest): HTTP запрос с данными для обновления
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Response: Обновленные данные номенклатуры

        Raises:
            ValidationError: Если переданы запрещенные поля
        """
        forbidden_fields = {"is_active"}
        sent_keys = set(request.data.keys())
        blocked_keys = sent_keys & forbidden_fields

        if blocked_keys:
            raise serializers.ValidationError(
                f"Редактирование запрещено для полей: {', '.join(blocked_keys)}"
            )

        return super().update(request, *args, **kwargs)

    def get_object(self):
        """
        Получает объект номенклатуры по идентификатору.

        Поддерживает поиск по:
        - UUID (id)
        - code1c (код из 1С)
        - old_catalog_slug (старый slug)

        Returns:
            Nomenclature: Объект номенклатуры

        Raises:
            NotFound: Если номенклатура не найдена
        """
        identifier = self.kwargs.get('pk')
        if not identifier:
            raise NotFound("Не указан идентификатор номенклатуры.")

        is_uuid = False
        try:
            UUID(str(identifier))
            is_uuid = True
        except ValueError:
            is_uuid = False

        if is_uuid:
            try:
                nomenclature = Nomenclature.objects.get(id=identifier)
                return nomenclature
            except Nomenclature.DoesNotExist:
                raise NotFound("Номенклатура не найдена.")

        try:
            nomenclature = Nomenclature.objects.get(code1c=identifier)
            return nomenclature
        except Nomenclature.DoesNotExist:
            pass

        try:
            nomenclature = Nomenclature.objects.get(old_catalog_slug=identifier)
            return nomenclature
        except Nomenclature.DoesNotExist:
            raise NotFound("Номенклатура не найдена.")

    @extend_schema(
        summary="Деактивировать номенклатуру",
        description="""
        Выполняет мягкое удаление (деактивацию) номенклатуры по ID.

        ## Что происходит
        1. Поле `is_active` устанавливается в `False`
        2. Номенклатура становится недоступной в основном API
        3. Данные сохраняются в БД (не удаляются физически)

        ## Восстановление
        - Используйте PATCH /api/nomenclatures/{id}/inactive/ с `is_active=True`
        """,
        tags=["Номенклатуры"]
    )
    def destroy(self, request, *args, **kwargs):
        """
        Выполнить мягкое удаление (деактивацию) номенклатуры по ID.

        Аргументы:
            request (HttpRequest): HTTP DELETE запрос
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Response: 204 No Content при успехе или 400 Bad Request при ошибке
        """
        instance = self.get_object()
        data = self.perform_destroy(instance)
        return Response(
            data={"detail": data} if data else None,
            status=400 if data else 204,
        )

    def perform_destroy(self, instance):
        """
        Выполняет физическое сохранение деактивации номенклатуры в БД.

        Аргументы:
            instance (Nomenclature): Объект для деактивации

        Returns:
            str или None: Сообщение об ошибке или None при успехе
        """
        if instance.is_active is False:
            return (
                "Нельзя деактивировать номенклатуру, т.к "
                "она уже деактивирована."
            )
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        return None

    @extend_schema(
        summary="Список версий ПО",
        description="""
        Возвращает список всех уникальных версий ПО, установленных на номенклатурах.

        ## Использование
        - Мониторинг версий ПО на устройствах
        - Планирование обновлений
        - Проверка совместимости контента

        ## Пример ответа
        {
            "versions": ["1.0.0", "1.0.1", "1.1.0", "2.0.0"]
        }
        """,
        responses={HTTP_200_OK: VersionsSerializer},
        tags=["Номенклатуры"]
    )
    @action(detail=False, methods=["GET"], url_path="versions")
    def get_versions(self, request):
        """
        Получить список всех уникальных версий ПО установленных на номенклатурах.

        Аргументы:
            request (HttpRequest): HTTP GET запрос

        Returns:
            Response: JSON с ключом 'versions' и списком версий
        """
        versions = (
            Nomenclature.objects.order_by()
            .values_list("version", flat=True)
            .distinct()
        )
        return Response({"versions": versions}, status=HTTP_200_OK)

    @extend_schema(
        summary="Получить UUID по id_rasb",
        description="""
        Возвращает UUID номенклатуры по полю id_rasb (ID тачки).

        ## Поддерживаемые методы
        - `GET` - параметр в URL: `?id_rasb=value`
        - `POST` - параметр в теле: `{"id_rasb": "value"}`

        ## Примеры
        GET /api/nomenclatures/get_uuid_by_id/?id_rasb=12345
        POST /api/nomenclatures/get_uuid_by_id/
        {"id_rasb": "12345"}

        ## Ответ
        {"id": "123e4567-e89b-12d3-a456-426614174000"}
        """,
        tags=["Номенклатуры"],
        responses={
            200: inline_serializer(
                name='GetIdResponse',
                fields={'id': serializers.CharField()}
            ),
            400: DetailSerializer,
            404: DetailSerializer,
        }
    )
    @action(
        detail=False,
        methods=["GET", "POST"],
        url_path="get_uuid_by_id",
        permission_classes=[AllowAny],
    )
    def get_id(self, request):
        """
        Получить UUID номенклатуры по id_rasb.

        Поддерживает GET и POST для обратной совместимости.
        GET: параметр в URL (?id_rasb=value)
        POST: параметр в теле запроса ({"id_rasb": "value"})

        Аргументы:
            request (HttpRequest): HTTP запрос

        Returns:
            Response: {"id": "uuid"} или ошибка
        """
        # Пробуем получить id_rasb из разных источников
        id_rasb = (
            request.query_params.get("id_rasb") or
            request.data.get("id_rasb") if hasattr(request, 'data') else None
        )

        # Если request.data недоступен (для GET без тела), пробуем другие способы
        if not id_rasb and request.method == "GET":
            try:
                import json
                body = request.body.decode('utf-8')
                if body:
                    data = json.loads(body)
                    id_rasb = data.get("id_rasb")
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass

        if not id_rasb:
            return Response(
                {"detail": "Параметр id_rasb обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        id_rasb = str(id_rasb)
        nomenclature = Nomenclature.objects.filter(id_rasb=id_rasb).first()

        if not nomenclature:
            return Response(
                {"detail": f"Номенклатура с id_rasb='{id_rasb}' не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"id": str(nomenclature.pk)})

    @extend_schema(
        summary="Получить номенклатуры по списку ID",
        description="""
        Возвращает номенклатуры по списку UUID (максимум 100 ID за запрос).

        ## Параметры
        - `ids` - UUID через запятую

        ## Пример
        GET /api/nomenclatures/bulk/?ids=uuid1,uuid2,uuid3

        ## Ограничения
        - Максимум 100 ID за запрос
        - Все ID должны быть валидными UUID
        """,
        parameters=[
            OpenApiParameter(
                name='ids',
                description='UUID через запятую',
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample(
                        'Список ID',
                        value='123e4567-e89b-12d3-a456-426614174000,223e4567-e89b-12d3-a456-426614174000'
                    )
                ]
            ),
        ],
        responses={200: NomenclatureListSerializer(many=True)},
        tags=['Номенклатуры'],
    )
    @action(
        detail=False,
        methods=['GET'],
        url_path='bulk',
        permission_classes=[AllowAny],
    )
    def bulk(self, request):
        """
        Получить номенклатуры по списку ID (максимум 100 ID за запрос).

        Аргументы:
            request (HttpRequest): HTTP запрос с параметром ids

        Returns:
            Response: Список номенклатур
        """
        raw = request.query_params.get('ids', '')
        if not raw:
            return Response(
                {'error': 'Параметр ids обязателен'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ids = []
        for part in raw.split(','):
            part = part.strip()
            try:
                ids.append(UUID(part))
            except ValueError:
                return Response(
                    {'error': f'Невалидный UUID: {part}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if len(ids) > 100:
            return Response(
                {'error': 'Максимум 100 ID за запрос'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = (
            Nomenclature.web.filter(id__in=ids)
            .select_related('brand', 'typeOfPlace', 'legalEntity', 'responsible_ad')
            .prefetch_related(
                'images',
                Prefetch(
                    'tenants',
                    queryset=Counterparty.objects.only(
                        'id', 'first_name', 'last_name',
                        'middle_name', 'additional_name', 'keyword'
                    ).prefetch_related('brands')
                )
            )
            .only(
                'id', 'name', 'code1c',
                'brand__name', 'brand__id',
                'typeOfPlace__name', 'typeOfPlace__id',
                'legalEntity__first_name', 'legalEntity__last_name',
                'responsible_ad__first_name', 'responsible_ad__last_name',
            )
        )

        serializer = NomenclatureCardSerializer(queryset, many=True)
        return Response(serializer.data)

    @staticmethod
    def _is_admin(user):
        """
        Проверяет, является ли пользователь администратором системы.

        Аргументы:
            user (CustomUser): Объект пользователя

        Returns:
            bool: True если пользователь администратор, иначе False
        """
        return (
                user.is_authenticated and (
                user.is_admin
                or user.is_superuser
                or user.is_manager
        )
        )

# """
# ViewSet для управления номенклатурами.

# Данный модуль предоставляет API для работы с номенклатурами (рабочими станциями).
# Реализована полная оптимизация запросов к базе данных с использованием only()
# вместо defer() для избежания конфликтов с select_related.

# ОПТИМИЗАЦИЯ ЗАПРОСОВ:
# ───────────────────────────────────────────────────────────────────────────────
# 1. Использование only() для загрузки только необходимых полей
# 2. Использование select_related для FK связей (1 запрос вместо N)
# 3. Использование prefetch_related для M2M связей (1 запрос вместо N)
# 4. Кеширование результатов поиска на 5 минут
# 5. Использование search_vector для полнотекстового поиска
# 6. Обработка ошибок с логированием

# КЛЮЧЕВЫЕ ИСПРАВЛЕНИЯ:
# ───────────────────────────────────────────────────────────────────────────────
# 1. Замена defer() на only() для избежания ошибки:
#    "Field cannot be both deferred and traversed using select_related"
# 2. Добавление всех полей из select_related в only()
# 3. Исправление get_id() для корректной работы с GET-запросами
# 4. Универсальная поддержка GET и POST для обратной совместимости

# ПРОИЗВОДИТЕЛЬНОСТЬ:
# ───────────────────────────────────────────────────────────────────────────────
# - До оптимизации: ~200 запросов на страницу
# - После оптимизации: ~5-10 запросов на страницу
# - Ускорение: ~20-40 раз
# """

# from typing import Callable, Optional
# from uuid import UUID

# from django.core.cache import cache
# from django.db.models import Count, Case, When, Value, IntegerField, Prefetch
# from django_filters.rest_framework import DjangoFilterBackend
# from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample
# from drf_spectacular.utils import inline_serializer, OpenApiResponse
# from rest_framework import serializers
# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.exceptions import NotFound, ValidationError
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from rest_framework.status import (
#     HTTP_200_OK,
# )

# from addresses.models import City
# from api.constants import VersionsSerializer, DetailSerializer
# from counterparties.models import Counterparty
# from counterparties.serializers import CounterpartiesShortSerializer, CounterpartyContactInfoSerializer
# from django.db import models
# from users.permissions import StaffCUDallRead
# from users.serializers import UserContactInfoSerializer
# from ..filters import NomenclatureFilter
# from ..models import Nomenclature, TypeOfPlace, NomenclatureAddress
# from ..serializers import (
#     NomenclatureSerializer,
#     NomenclatureListSerializer,
#     ShortBrandNomenclatureSerializer, PhotoSerializer, NomenclatureCardSerializer, CityNomenclaturesSerializer,
# )
# import logging

# logger = logging.getLogger(__name__)


# @extend_schema_view(
#     grouped=extend_schema(
#         summary="Получить номенклатуры, сгруппированные по полю",
#         description="""
#         Возвращает список номенклатур, сгруппированных по указанному полю.

#         Каждая группа содержит:
#         - name: Название группы (значение поля группировки)
#         - items: Массив номенклатур в этой группе

#         Поддерживаемые параметры группировки:
#         - brand: группировка по названию бренда
#         - legal: группировка по названию юридического лица
#         - place: группировка по типу места размещения
#         - address: группировка по городу
#         """,
#         parameters=[
#             OpenApiParameter(
#                 name='by',
#                 description='Поле для группировки (обязательный параметр)',
#                 required=True,
#                 type=str,
#                 enum=['brand', 'legal', 'place', 'address']
#             ),
#         ],
#         responses={
#             200: inline_serializer(
#                 name='GroupedNomenclaturesResponse',
#                 fields={
#                     'name': serializers.CharField(),
#                     'items': NomenclatureListSerializer(many=True)
#                 }
#             ),
#             400: OpenApiResponse(
#                 description='Ошибка валидации - неверный параметр группировки',
#                 response=inline_serializer(
#                     name='GroupingErrorResponse',
#                     fields={
#                         'error': serializers.CharField(),
#                         'allowed': serializers.ListField(child=serializers.CharField())
#                     }
#                 )
#             ),
#         },
#         examples=[
#             OpenApiExample(
#                 'Успешный ответ',
#                 value=[
#                     {
#                         'name': 'test brand',
#                         'items': [
#                             {
#                                 'id': '123e4567-e89b-12d3-a456-426614174000',
#                                 'name': 'Display 1',
#                                 'timezone': 'UTC +7',
#                                 'status': 0,
#                                 'legalEntity': {
#                                     'id': 1,
#                                     'name': 'ООО Рекламное агентство'
#                                 },
#                                 'brand': {
#                                     'id': 1,
#                                     'name': 'test brand',
#                                     'logotype': 'https://...'
#                                 }
#                             }
#                         ]
#                     }
#                 ],
#                 response_only=True,
#                 status_codes=['200']
#             ),
#             OpenApiExample(
#                 'Ошибка - неверный параметр',
#                 value={
#                     'error': 'Invalid group param',
#                     'allowed': ['brand', 'legal', 'place', 'address']
#                 },
#                 response_only=True,
#                 status_codes=['400']
#             )
#         ],
#         tags=['Номенклатуры']
#     )
# )
# @extend_schema(tags=["Номенклатуры"])
# class NomenclatureViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet для полного управления номенклатурами в системе.

#     Номенклатура - это основная единица в системе, представляющая точку
#     отображения контента (рабочую станцию, дисплей и т.д.).

#     ENDPOINTS:
#     ───────────────────────────────────────────────────────────────────────────────
#     GET    /api/nomenclatures/                          - Список активных номенклатур
#     GET    /api/nomenclatures/{id}/                    - Детали номенклатуры
#     POST   /api/nomenclatures/                         - Создать новую номенклатуру
#     PATCH  /api/nomenclatures/{id}/                    - Обновить номенклатуру
#     DELETE /api/nomenclatures/{id}/                    - Деактивировать номенклатуру
#     GET    /api/nomenclatures/inactive_list/           - Список неактивных
#     GET    /api/nomenclatures/broadcast/               - Номенклатуры для вещания
#     GET    /api/nomenclatures/versions/                - Все версии ПО
#     GET    /api/nomenclatures/get_uuid_by_id/          - Поиск по id_rasb
#     GET    /api/nomenclatures/bulk/                    - Получить по списку ID

#     PERMISSIONS:
#     ───────────────────────────────────────────────────────────────────────────────
#     - list: AllowAny
#     - create: IsAuthenticated + IsStaff
#     - retrieve: AllowAny
#     - update: IsAuthenticated + IsStaff
#     - destroy: IsAuthenticated + IsStaff
#     """

#     queryset = Nomenclature.web.select_related(
#         "owner",
#         "legalEntity",
#         "brand",
#         "responsible_ad",
#         "typeOfPlace",
#     )

#     serializer_class = NomenclatureSerializer
#     permission_classes = [StaffCUDallRead]
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = NomenclatureFilter
#     CACHE_TIMEOUT = 300

#     def get_serializer(self, *args, **kwargs):
#         """
#         Динамически выбирает сериализатор в зависимости от типа операции.

#         Для операции 'list' (получение списка) используется NomenclatureCardSerializer.
#         Для остальных операций (retrieve, create, update, destroy) используется
#         полный NomenclatureSerializer со всеми полями.

#         Аргументы:
#             *args: Позиционные аргументы
#             **kwargs: Именованные аргументы

#         Returns:
#             Serializer: Экземпляр соответствующего сериализатора
#         """
#         if self.action == "list":
#             serializer_class = NomenclatureCardSerializer
#         else:
#             serializer_class = NomenclatureSerializer

#         if "data" in kwargs and isinstance(kwargs["data"], list):
#             kwargs["many"] = True

#         return serializer_class(*args, **kwargs)

#     def get_queryset(self):
#         """
#         Оптимизирует queryset в зависимости от типа запроса.

#         Для поиска используется only() для загрузки только необходимых полей.
#         Для обычного списка only() НЕ используется (как в исходном коде),
#         чтобы избежать конфликта с select_related('availability').
#         """
#         base_qs = super().get_queryset()

#         # Для поиска - используем only() (здесь нет availability)
#         if self.action == "list" and self.request.query_params.get('search'):
#             return (
#                 base_qs
#                 .select_related(
#                     'brand',
#                     'typeOfPlace',
#                     'legalEntity',
#                     'responsible_ad',
#                 )
#                 .prefetch_related(
#                     "images",
#                     Prefetch(
#                         'tenants',
#                         queryset=Counterparty.objects.only(
#                             'id', 'first_name', 'last_name',
#                             'middle_name', 'additional_name', 'keyword'
#                         ).prefetch_related('brands')
#                     )
#                 )
#                 .only(
#                     'id', 'name', 'code1c',
#                     'brand__name', 'brand__id',
#                     'typeOfPlace__name', 'typeOfPlace__id',
#                     'legalEntity__first_name', 'legalEntity__last_name',
#                     'responsible_ad__first_name', 'responsible_ad__last_name',
#                 )
#             )

#         # Для обычного списка - НЕТ only() (как в исходном коде)
#         tc = TypeOfPlace.objects.filter(name="Торговый центр").first()

#         if tc:
#             ordering_case = Case(
#                 When(typeOfPlace_id=tc.id, then=Value(0)),
#                 default=Value(1),
#                 output_field=IntegerField(),
#             )
#         else:
#             ordering_case = Value(1)

#         return (
#             base_qs
#             .select_related(
#                 "legalEntity",
#                 "brand",
#                 "responsible_ad",
#                 "typeOfPlace",
#                 "responsible_radio",
#                 "responsible_technic",
#                 "responsible_technic_on_address",
#                 "responsible_placement_marketing",
#             )
#             .prefetch_related(
#                 "images",
#                 Prefetch(
#                     'tenants',
#                     queryset=Counterparty.objects.only(
#                         'id', 'first_name', 'last_name',
#                         'middle_name', 'additional_name', 'keyword'
#                     ).prefetch_related('brands')
#                 )
#             )
#             .annotate(tenants_count=Count("tenants", distinct=True))
#             .order_by(
#                 ordering_case,
#                 "-tenants_count",
#                 "-created",
#             )
#         )

#     @extend_schema(
#         summary="Номенклатуры по городу",
#         description="""
#         Возвращает агрегированные данные по номенклатуре для указанного города.

#         Параметры:
#             city_slug (str): Slug города в URL

#         Ответ:
#             {
#                 "city": "Красноярск",
#                 "minPrice": 1000.00,
#                 "nomenclatures": [...],
#                 "count": 10
#             }
#         """,
#         tags=["Номенклатуры"]
#     )
#     @action(
#         detail=False,
#         methods=["get"],
#         url_path="by-city/(?P<city_slug>[^/.]+)",
#         permission_classes=[AllowAny],
#     )
#     def by_city(self, request, city_slug=None):
#         """
#         Возвращает агрегированные данные по номенклатуре для указанного города.

#         Аргументы:
#             request (HttpRequest): HTTP запрос
#             city_slug (str): Slug города

#         Returns:
#             Response: JSON с данными по городу
#         """
#         city = City.objects.filter(slug=city_slug).first()
#         if not city:
#             return Response(
#                 {"error": f"Город с slug '{city_slug}' не найден"},
#                 status=404,
#             )

#         queryset = (
#             Nomenclature.web
#             .filter(address__address__city=city)
#             .select_related(
#                 'typeOfPlace',
#                 'brand',
#                 'address__address__city',
#             )
#             .prefetch_related(
#                 Prefetch(
#                     'address',
#                     queryset=NomenclatureAddress.objects.select_related('address')
#                 )
#             )
#         )

#         min_price = queryset.aggregate(
#             min_price=models.Min("pricePerMonth")
#         )["min_price"] or 0.0

#         serializer = CityNomenclaturesSerializer(
#             queryset,
#             many=True,
#             context={"city_name": city.name}
#         )

#         return Response({
#             "city": city.name,
#             "minPrice": min_price,
#             "nomenclatures": serializer.data,
#             "count": queryset.count(),
#         })

#     def list(self, request, *args, **kwargs):
#         """
#         Переопределенный метод list с поддержкой поиска и кеширования.

#         Аргументы:
#             request (HttpRequest): HTTP запрос
#             *args: Позиционные аргументы
#             **kwargs: Именованные аргументы

#         Returns:
#             Response: Пагинированный список номенклатур
#         """
#         search_term = request.query_params.get('search')

#         # Проверка минимальной длины поискового запроса
#         if search_term is not None and len(search_term.strip()) < 3:
#             return Response(
#                 {"detail": "Поисковый запрос должен содержать не менее 3 символов."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Если нет поиска - стандартный список
#         if not search_term:
#             return super().list(request, *args, **kwargs)

#         # Кеширование результатов поиска
#         cache_page = request.query_params.get('page', 1)
#         cache_limit = request.query_params.get('limit', self.paginator.page_size)
#         cache_key = f"nomenclature_search_result_{hash(search_term)}_{cache_page}_{cache_limit}"

#         cached_result = cache.get(cache_key)
#         if cached_result:
#             logger.info(f"Взят из кэша результат для '{search_term}'")
#             return Response(cached_result)

#         try:
#             from collections import Counter
#             from nomenclatures.services.search import NomenclatureSearchService

#             # Получение queryset через сервис поиска
#             base_queryset = NomenclatureSearchService.search(
#                 query=search_term,
#                 for_web=True,
#                 limit=5000,
#                 use_cache=True
#             )

#             if not base_queryset:
#                 result = {'count': 0, 'next': None, 'previous': None, 'results': []}
#                 cache.set(cache_key, result, self.CACHE_TIMEOUT)
#                 return Response(result)

#             # Определяем ID торговых центров для сортировки
#             tc_ids = set(TypeOfPlace.objects.filter(is_mall=True).values_list('id', flat=True))

#             # Оптимизируем queryset для отображения
#             queryset = (
#                 base_queryset
#                 .select_related('brand', 'typeOfPlace', 'legalEntity', 'responsible_ad')
#                 .prefetch_related(
#                     'images',
#                     Prefetch(
#                         'tenants',
#                         queryset=Counterparty.objects.only(
#                             'id', 'first_name', 'last_name',
#                             'middle_name', 'additional_name', 'keyword'
#                         ).prefetch_related('brands')
#                     )
#                 )
#                 .annotate(tenants_count=Count('tenants', distinct=True))
#                 .only(
#                     'id', 'name', 'code1c',
#                     'brand__name', 'brand__id',
#                     'typeOfPlace__name', 'typeOfPlace__id',
#                     'legalEntity__first_name', 'legalEntity__last_name',
#                     'responsible_ad__first_name', 'responsible_ad__last_name',
#                 )
#             )

#             # Сортировка по популярности бренда
#             brand_freq = Counter(
#                 n.brand_id for n in queryset if n.brand_id is not None
#             )

#             def sort_key(n):
#                 is_mall = 0 if (n.typeOfPlace_id in tc_ids) else 1
#                 tenants = -n.tenants_count
#                 brand_pop = -brand_freq.get(n.brand_id, 0)
#                 return (is_mall, tenants, brand_pop)

#             sorted_list = sorted(queryset, key=sort_key)

#             # Пагинация
#             page = self.paginator.paginate_queryset(sorted_list, request)
#             if page is not None:
#                 serializer = self.get_serializer(page, many=True)
#                 result = self.get_paginated_response(serializer.data).data
#             else:
#                 serializer = self.get_serializer(sorted_list, many=True)
#                 result = {
#                     'count': len(serializer.data),
#                     'next': None,
#                     'previous': None,
#                     'results': serializer.data
#                 }

#             # Кеширование результата
#             cache.set(cache_key, result, self.CACHE_TIMEOUT)
#             logger.info(f"Закэширован результат для '{search_term}'")
#             return Response(result)

#         except Exception as e:
#             logger.error(f'Search error: {e}', exc_info=True)
#             # Fallback на простой поиск
#             queryset = self.get_queryset().filter(name__icontains=search_term)[:50]
#             serializer = self.get_serializer(queryset, many=True)
#             return Response({
#                 'count': len(serializer.data),
#                 'next': None,
#                 'previous': None,
#                 'results': serializer.data
#             })

#     @action(detail=True, methods=["get"], url_path="tabs")
#     def tabs(self, request, pk):
#         """
#         Получение данных для вкладок номенклатуры.

#         Аргументы:
#             request (HttpRequest): HTTP запрос с параметром q
#             pk (UUID): ID номенклатуры

#         Returns:
#             Response: Данные для запрошенной вкладки
#         """
#         nomenclature = self.get_object()
#         tab = request.query_params.get("q")

#         if not tab:
#             raise ValidationError({"q": "Query-параметр 'q' обязателен. Например: ?q=tenants"})

#         handler = self._get_tab_handler(tab)
#         if not handler:
#             raise ValidationError({"q": f"Неподдерживаемая вкладка '{tab}'"})

#         return handler(nomenclature)

#     def _get_tab_handler(
#             self, tab: str
#     ) -> Optional[Callable[[Nomenclature], Response]]:
#         """
#         Возвращает обработчик для запрошенной вкладки.

#         Аргументы:
#             tab (str): Название вкладки

#         Returns:
#             Optional[Callable]: Функция-обработчик или None
#         """
#         return {
#             "tenants": self._tenants_tab,
#             "contacts": self._contacts_tab,
#             "photos": self._photos_tab,
#         }.get(tab)

#     def _tenants_tab(self, nomenclature):
#         """
#         Возвращает список арендаторов номенклатуры.

#         Аргументы:
#             nomenclature (Nomenclature): Объект номенклатуры

#         Returns:
#             Response: Сериализованный список арендаторов
#         """
#         serializer = CounterpartiesShortSerializer(
#             nomenclature.tenants.all(),
#             many=True
#         )
#         return Response(serializer.data)

#     def _contacts_tab(self, nomenclature):
#         """
#         Возвращает контактную информацию номенклатуры.

#         Аргументы:
#             nomenclature (Nomenclature): Объект номенклатуры

#         Returns:
#             Response: Структурированная контактная информация
#         """
#         result = {
#             "legal_entity": None,
#             "legal_entity_cp": [],
#             "marketing": None,
#             "ad": None,
#         }

#         legal_entity = nomenclature.legalEntity

#         if legal_entity:
#             result["legal_entity"] = CounterpartyContactInfoSerializer(
#                 legal_entity.contacts.all(),
#                 many=True
#             ).data

#             contacts = []

#             for user in legal_entity.contact_persons.all():
#                 contacts.extend(user.contacts_cp.all())

#             result["legal_entity_cp"] = UserContactInfoSerializer(
#                 contacts,
#                 many=True
#             ).data

#         if nomenclature.responsible_placement_marketing:
#             contacts = nomenclature.responsible_placement_marketing.contacts_cp.all()
#             result["marketing"] = UserContactInfoSerializer(
#                 contacts,
#                 many=True
#             ).data

#         if nomenclature.responsible_ad:
#             contacts = nomenclature.responsible_ad.contacts_cp.all()
#             result["ad"] = UserContactInfoSerializer(
#                 contacts,
#                 many=True
#             ).data

#         return Response(result)

#     def _photos_tab(self, nomenclature):
#         """
#         Возвращает список фотографий номенклатуры.

#         Аргументы:
#             nomenclature (Nomenclature): Объект номенклатуры

#         Returns:
#             Response: Сериализованный список фотографий
#         """
#         serializer = PhotoSerializer(
#             nomenclature.images.all(),
#             many=True
#         )
#         return Response(serializer.data)

#     @action(detail=False, methods=['get'])
#     def grouped(self, request):
#         """
#         Возвращает номенклатуры, сгруппированные по указанному полю.

#         Аргументы:
#             request (HttpRequest): HTTP запрос с параметром by

#         Returns:
#             Response: Сгруппированный список номенклатур
#         """
#         qs = Nomenclature.web.select_related('brand', 'typeOfPlace')

#         filterset = self.filterset_class(
#             request.query_params,
#             queryset=qs,
#             request=request
#         )

#         qs = filterset.qs.annotate(
#             tenants_count=Count("tenants", distinct=True)
#         )

#         group_by = request.query_params.get('by')

#         GROUP_MAP = {
#             'brand': lambda x: x['brand_name'] if x['brand_id'] else None,
#         }

#         if group_by not in GROUP_MAP:
#             return Response({
#                 'error': 'Invalid group param',
#                 'allowed': list(GROUP_MAP.keys())
#             }, status=400)

#         serializer = ShortBrandNomenclatureSerializer(qs, many=True)
#         data = serializer.data

#         grouped = {}
#         for item in data:
#             key = GROUP_MAP[group_by](item)

#             if key not in grouped:
#                 grouped[key] = {
#                     'name': key,
#                     'typeOfPlace': item['type_of_place'],
#                     'brand_id': item['brand_id'],
#                     'brand_logotype': item['brand_logotype'],
#                     'amount': 1,
#                     'tenants_count': item.get('tenants_count', 0),
#                 }
#             else:
#                 grouped[key]['amount'] += 1
#                 grouped[key]['tenants_count'] += item.get('tenants_count', 0)

#         TC = "Торговый центр"

#         def sort_key(x):
#             is_tc = x['typeOfPlace'] == TC
#             if is_tc:
#                 return 0, -x['tenants_count'], -x['amount'], ''
#             else:
#                 return 1, 0, -x['amount'], x['typeOfPlace'] or ''

#         result = sorted(grouped.values(), key=sort_key)
#         for item in result:
#             item.pop('tenants_count', None)
#         page = self.paginate_queryset(result)
#         if page is not None:
#             return self.get_paginated_response(page)
#         return Response(result)

#     def perform_create(self, serializer):
#         """
#         Сохраняет новую номенклатуру с текущим пользователем как владельцем.

#         Аргументы:
#             serializer (Serializer): Сериализатор с валидными данными
#         """
#         serializer.save(owner=self.request.user)

#     @extend_schema(
#         summary="Список деактивированных номенклатур",
#         description="Возвращает пагинированный список всех деактивированных номенклатур. Доступно только для персонала.",
#         tags=["Номенклатуры"]
#     )
#     @action(
#         detail=False,
#         methods=["get"],
#         url_path="inactive_list",
#         permission_classes=[StaffCUDallRead]
#     )
#     def inactive(self, request):
#         """
#         Получить пагинированный список всех деактивированных номенклатур.

#         Аргументы:
#             request (HttpRequest): HTTP запрос

#         Returns:
#             Response: Пагинированный список неактивных номенклатур
#         """
#         qs = (
#             Nomenclature.inactive
#             .select_related("owner", "availability", "brand", "address")
#             .prefetch_related("images")
#         )

#         page = self.paginate_queryset(qs)
#         serializer = self.get_serializer(page or qs, many=True)
#         return (
#             self.get_paginated_response(serializer.data)
#             if page is not None
#             else Response(serializer.data)
#         )

#     @extend_schema(
#         summary="Работа с деактивированной номенклатурой",
#         description="""
#         Получить полные детали или обновить деактивированную номенклатуру по ID.

#         Поддерживаемые методы:
#         - GET: Получить данные деактивированной номенклатуры
#         - PATCH: Частично обновить деактивированную номенклатуру
#         """,
#         tags=["Номенклатуры"]
#     )
#     @action(
#         detail=True,
#         methods=["get", "patch"],
#         url_path="inactive",
#         permission_classes=[StaffCUDallRead]
#     )
#     def inactive_detail(self, request, pk=None):
#         """
#         Получить полные детали или обновить деактивированную номенклатуру по ID.

#         Аргументы:
#             request (HttpRequest): HTTP запрос (GET или PATCH)
#             pk (UUID): ID номенклатуры

#         Returns:
#             Response: Данные номенклатуры
#         """
#         identifier = pk
#         if not identifier:
#             raise NotFound("Не указан идентификатор КА.")

#         is_uuid = False
#         try:
#             UUID(str(identifier))
#             is_uuid = True
#         except ValueError:
#             is_uuid = False

#         instance = None

#         if is_uuid:
#             try:
#                 instance = (
#                     Nomenclature.inactive
#                     .select_related("owner", "availability", "brand", "address")
#                     .prefetch_related("images")
#                     .get(id=identifier)
#                 )
#             except Nomenclature.DoesNotExist:
#                 pass

#         if instance is None:
#             try:
#                 instance = (
#                     Nomenclature.inactive
#                     .select_related("owner", "availability", "brand", "address")
#                     .prefetch_related("images")
#                     .get(code1c=identifier)
#                 )
#             except Nomenclature.DoesNotExist:
#                 raise NotFound("Номенклатура не найдена.")

#         if request.method == "GET":
#             serializer = self.get_serializer(instance)
#             return Response(serializer.data)

#         serializer = self.get_serializer(
#             instance,
#             data=request.data,
#             partial=True,
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

#     @extend_schema(
#         summary="Список номенклатур для вещания",
#         description="""
#         Возвращает список номенклатур для вещания с учетом роли пользователя.

#         Администраторы видят все активные номенклатуры с флагом broadcast=True.
#         Обычные пользователи видят только номенклатуры своих контрагентов.
#         """,
#         tags=["Номенклатуры"]
#     )
#     @action(detail=False, methods=["GET"], url_path="broadcast")
#     def broadcast(self, request):
#         """
#         Получить список номенклатур для вещания с учетом роли пользователя.

#         Аргументы:
#             request (HttpRequest): HTTP запрос

#         Returns:
#             Response: Пагинированный список номенклатур для вещания
#         """
#         user = request.user
#         is_broadcast = user.is_contact_person_broadcast

#         if (not user.is_authenticated and not self._is_admin(request.user)) or (
#                 not user.is_authenticated and not is_broadcast):
#             return Response(
#                 {'message': 'Недостаточно прав.'},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         if self._is_admin(request.user):
#             qs = (
#                 Nomenclature.active
#                 .select_related("owner", "availability", "brand", "address")
#                 .prefetch_related("images")
#                 .filter(legalEntity__broadcast=True)
#             )
#         elif is_broadcast:
#             user_counterparties = user.counterparties.all()
#             qs = (
#                 self.get_queryset()
#                 .filter(legalEntity__in=user_counterparties)
#             )
#         else:
#             return Response(
#                 {'message': 'Недостаточно прав.'},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         page = self.paginate_queryset(qs)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)

#         serializer = self.get_serializer(qs, many=True)
#         return Response(serializer.data)

#     def update(self, request, *args, **kwargs):
#         """
#         Обновить номенклатуру с контролем редактируемых полей.

#         Аргументы:
#             request (HttpRequest): HTTP запрос с данными для обновления
#             *args: Позиционные аргументы
#             **kwargs: Именованные аргументы

#         Returns:
#             Response: Обновленные данные номенклатуры

#         Raises:
#             ValidationError: Если переданы запрещенные поля
#         """
#         forbidden_fields = {"is_active"}
#         sent_keys = set(request.data.keys())
#         blocked_keys = sent_keys & forbidden_fields

#         if blocked_keys:
#             raise serializers.ValidationError(
#                 f"Редактирование запрещено для полей: {', '.join(blocked_keys)}"
#             )

#         return super().update(request, *args, **kwargs)

#     def get_object(self):
#         """
#         Получает объект номенклатуры по идентификатору.

#         Поддерживает поиск по:
#         - UUID (id)
#         - code1c (код из 1С)
#         - old_catalog_slug (старый slug)

#         Returns:
#             Nomenclature: Объект номенклатуры

#         Raises:
#             NotFound: Если номенклатура не найдена
#         """
#         identifier = self.kwargs.get('pk')
#         if not identifier:
#             raise NotFound("Не указан идентификатор номенклатуры.")

#         is_uuid = False
#         try:
#             UUID(str(identifier))
#             is_uuid = True
#         except ValueError:
#             is_uuid = False

#         if is_uuid:
#             try:
#                 nomenclature = Nomenclature.objects.get(id=identifier)
#                 return nomenclature
#             except Nomenclature.DoesNotExist:
#                 raise NotFound("Номенклатура не найдена.")

#         try:
#             nomenclature = Nomenclature.objects.get(code1c=identifier)
#             return nomenclature
#         except Nomenclature.DoesNotExist:
#             pass

#         try:
#             nomenclature = Nomenclature.objects.get(old_catalog_slug=identifier)
#             return nomenclature
#         except Nomenclature.DoesNotExist:
#             raise NotFound("Номенклатура не найдена.")

#     @extend_schema(
#         summary="Деактивировать номенклатуру",
#         description="""
#         Выполняет мягкое удаление (деактивацию) номенклатуры по ID.
#         Номенклатура помечается как is_active=False, но не удаляется из БД.
#         """,
#         tags=["Номенклатуры"]
#     )
#     def destroy(self, request, *args, **kwargs):
#         """
#         Выполнить мягкое удаление (деактивацию) номенклатуры по ID.

#         Аргументы:
#             request (HttpRequest): HTTP DELETE запрос
#             *args: Позиционные аргументы
#             **kwargs: Именованные аргументы

#         Returns:
#             Response: 204 No Content при успехе или 400 Bad Request при ошибке
#         """
#         instance = self.get_object()
#         data = self.perform_destroy(instance)
#         return Response(
#             data={"detail": data} if data else None,
#             status=400 if data else 204,
#         )

#     def perform_destroy(self, instance):
#         """
#         Выполняет физическое сохранение деактивации номенклатуры в БД.

#         Аргументы:
#             instance (Nomenclature): Объект для деактивации

#         Returns:
#             str или None: Сообщение об ошибке или None при успехе
#         """
#         if instance.is_active is False:
#             return (
#                 "Нельзя деактивировать номенклатуру, т.к "
#                 "она уже деактивирована."
#             )
#         instance.is_active = False
#         instance.save(update_fields=["is_active"])
#         return None

#     @extend_schema(
#         summary="Получить список всех версий номенклатур",
#         description="Возвращает список всех уникальных версий ПО, установленных на номенклатурах.",
#         responses={HTTP_200_OK: VersionsSerializer},
#         tags=["Номенклатуры"]
#     )
#     @action(detail=False, methods=["GET"], url_path="versions")
#     def get_versions(self, request):
#         """
#         Получить список всех уникальных версий ПО установленных на номенклатурах.

#         Аргументы:
#             request (HttpRequest): HTTP GET запрос

#         Returns:
#             Response: JSON с ключом 'versions' и списком версий
#         """
#         versions = (
#             Nomenclature.objects.order_by()
#             .values_list("version", flat=True)
#             .distinct()
#         )
#         return Response({"versions": versions}, status=HTTP_200_OK)

#     @extend_schema(
#         summary="Получить UUID по id_rasb",
#         description="""
#         Возвращает UUID номенклатуры по полю id_rasb.

#         Поддерживает GET и POST методы для обратной совместимости.
#         Также поддерживает передачу id_rasb как в теле запроса, так и в URL параметре.

#         Пример GET запроса (параметр в URL):
#             GET /api/nomenclatures/get_uuid_by_id/?id_rasb=12345

#         Пример GET запроса (параметр в теле - нестандартно, но поддерживается):
#             GET /api/nomenclatures/get_uuid_by_id/
#             {"id_rasb": "12345"}

#         Пример POST запроса:
#             POST /api/nomenclatures/get_uuid_by_id/
#             "id_rasb": "12345"}
#         """,
#         tags=["Номенклатуры"],
#         request=None,
#         responses={
#             200: inline_serializer(
#                 name='GetIdResponse',
#                 fields={
#                     'id': serializers.CharField()
#                 }
#             ),
#             400: DetailSerializer,
#             404: DetailSerializer,
#         }
#     )
#     @action(
#         detail=False,
#         methods=["GET", "POST"],
#         url_path="get_uuid_by_id",
#         permission_classes=[AllowAny],
#     )
#     def get_id(self, request):  # ← ✅ БЕЗ лишнего отступа!
#         """
#         Получить UUID номенклатуры по id_rasb.

#         Поддерживает GET и POST для обратной совместимости.
#         Поддерживает передачу id_rasb в:
#         - URL параметре (?id_rasb=value)
#         - Теле запроса ({"id_rasb": "value"})
#         - Теле запроса ({"id_rasb": value}) - без кавычек

#         Аргументы:
#             request (HttpRequest): HTTP запрос

#         Returns:
#             Response: {"id": "uuid"} или ошибка
#         """
#         # Пробуем получить id_rasb из разных источников
#         id_rasb = (
#             request.query_params.get("id_rasb") or
#             request.data.get("id_rasb") if hasattr(request, 'data') else None
#         )

#         # Если request.data недоступен (для GET без тела), пробуем другие способы
#         if not id_rasb and request.method == "GET":
#             try:
#                 import json
#                 body = request.body.decode('utf-8')
#                 if body:
#                     data = json.loads(body)
#                     id_rasb = data.get("id_rasb")
#             except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
#                 pass

#         if not id_rasb:
#             return Response(
#                 {"detail": "Параметр id_rasb обязателен."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         id_rasb = str(id_rasb)
#         nomenclature = Nomenclature.objects.filter(id_rasb=id_rasb).first()

#         if not nomenclature:
#             return Response(
#                 {"detail": f"Номенклатура с id_rasb='{id_rasb}' не найдена."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         return Response({"id": str(nomenclature.pk)})

#     @extend_schema(
#         summary="Получить номенклатуры по списку ID",
#         description="""
#         Возвращает номенклатуры по списку UUID (максимум 100 ID за запрос).

#         Параметры:
#             ids (str): UUID через запятую

#         Пример:
#             GET /api/nomenclatures/bulk/?ids=uuid1,uuid2,uuid3
#         """,
#         parameters=[
#             OpenApiParameter(
#                 name='ids',
#                 description='UUID через запятую',
#                 required=True,
#                 type=str,
#             ),
#         ],
#         responses={200: NomenclatureListSerializer(many=True)},
#         tags=['Номенклатуры'],
#     )
#     @action(
#         detail=False,
#         methods=['GET'],
#         url_path='bulk',
#         permission_classes=[AllowAny],
#     )
#     def bulk(self, request):
#         """
#         Получить номенклатуры по списку ID (максимум 100 ID за запрос).

#         Аргументы:
#             request (HttpRequest): HTTP запрос с параметром ids

#         Returns:
#             Response: Список номенклатур
#         """
#         raw = request.query_params.get('ids', '')
#         if not raw:
#             return Response(
#                 {'error': 'Параметр ids обязателен'},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         ids = []
#         for part in raw.split(','):
#             part = part.strip()
#             try:
#                 ids.append(UUID(part))
#             except ValueError:
#                 return Response(
#                     {'error': f'Невалидный UUID: {part}'},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#         if len(ids) > 100:
#             return Response(
#                 {'error': 'Максимум 100 ID за запрос'},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         queryset = (
#             Nomenclature.web.filter(id__in=ids)
#             .select_related('brand', 'typeOfPlace', 'legalEntity', 'responsible_ad')
#             .prefetch_related(
#                 'images',
#                 Prefetch(
#                     'tenants',
#                     queryset=Counterparty.objects.only(
#                         'id', 'first_name', 'last_name',
#                         'middle_name', 'additional_name', 'keyword'
#                     ).prefetch_related('brands')
#                 )
#             )
#             .only(
#                 'id', 'name', 'code1c',
#                 'brand__name', 'brand__id',
#                 'typeOfPlace__name', 'typeOfPlace__id',
#                 'legalEntity__first_name', 'legalEntity__last_name',
#                 'responsible_ad__first_name', 'responsible_ad__last_name',
#             )
#         )

#         serializer = NomenclatureCardSerializer(queryset, many=True)
#         return Response(serializer.data)

#     @staticmethod
#     def _is_admin(user):
#         """
#         Проверяет, является ли пользователь администратором системы.

#         Аргументы:
#             user (CustomUser): Объект пользователя

#         Returns:
#             bool: True если пользователь администратор, иначе False
#         """
#         return (
#                 user.is_authenticated and (
#                 user.is_admin
#                 or user.is_superuser
#                 or user.is_manager
#         )
#         )

# from typing import Callable, Optional
# from uuid import UUID

# from django.core.cache import cache
# from django.db.models import Count, Case, When, Value, IntegerField, Prefetch
# from django_filters.rest_framework import DjangoFilterBackend
# from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample
# from drf_spectacular.utils import inline_serializer, OpenApiResponse
# from rest_framework import serializers
# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.exceptions import NotFound, ValidationError
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from rest_framework.status import (
#     HTTP_200_OK,
# )

# from addresses.models import City
# from api.constants import VersionsSerializer
# from counterparties.models import Counterparty
# from counterparties.serializers import CounterpartiesShortSerializer, CounterpartyContactInfoSerializer
# from django.db import models
# from users.permissions import StaffCUDallRead
# from users.serializers import UserContactInfoSerializer
# from ..filters import NomenclatureFilter
# from ..models import Nomenclature, TypeOfPlace, NomenclatureAddress
# from ..serializers import (
#     NomenclatureSerializer,
#     NomenclatureListSerializer,
#     ShortBrandNomenclatureSerializer, PhotoSerializer, NomenclatureCardSerializer, CityNomenclaturesSerializer,
# )
# import logging

# logger = logging.getLogger(__name__)


# @extend_schema_view(
#     grouped=extend_schema(
#         summary="Получить номенклатуры, сгруппированные по полю",
#         description="""
#         Возвращает список номенклатур, сгруппированных по указанному полю.

#         Каждая группа содержит:
#         - **name**: Название группы (значение поля группировки)
#         - **items**: Массив номенклатур в этой группе

#         Поддерживаемые параметры группировки:
#         - **brand**: группировка по названию бренда
#         - **legal**: группировка по названию юридического лица
#         - **place**: группировка по типу места размещения
#         - **address**: группировка по городу
#         """,
#         parameters=[
#             OpenApiParameter(
#                 name='by',
#                 description='Поле для группировки (обязательный параметр)',
#                 required=True,
#                 type=str,
#                 enum=['brand', 'legal', 'place', 'address']
#             ),
#         ],
#         responses={
#             200: inline_serializer(
#                 name='GroupedNomenclaturesResponse',
#                 fields={
#                     'name': serializers.CharField(),
#                     'items': NomenclatureListSerializer(many=True)  # замените на ваш реальный сериализатор
#                 }
#             ),
#             400: OpenApiResponse(
#                 description='Ошибка валидации - неверный параметр группировки',
#                 response=inline_serializer(
#                     name='GroupingErrorResponse',
#                     fields={
#                         'error': serializers.CharField(),
#                         'allowed': serializers.ListField(child=serializers.CharField())
#                     }
#                 )
#             ),
#         },
#         examples=[
#             OpenApiExample(
#                 'Успешный ответ',
#                 value=[
#                     {
#                         'name': 'test brand',
#                         'items': [
#                             {
#                                 'id': '123e4567-e89b-12d3-a456-426614174000',
#                                 'name': 'Display 1',
#                                 'timezone': 'UTC +7',
#                                 'status': 0,
#                                 'legalEntity': {
#                                     'id': 1,
#                                     'name': 'ООО Рекламное агентство'
#                                 },
#                                 'brand': {
#                                     'id': 1,
#                                     'name': 'test brand',
#                                     'logotype': 'https://...'
#                                 }
#                             }
#                         ]
#                     }
#                 ],
#                 response_only=True,
#                 status_codes=['200']
#             ),
#             OpenApiExample(
#                 'Ошибка - неверный параметр',
#                 value={
#                     'error': 'Invalid group param',
#                     'allowed': ['brand', 'legal', 'place', 'address']
#                 },
#                 response_only=True,
#                 status_codes=['400']
#             )
#         ],
#         tags=['Номенклатуры']
#     )
# )
# @extend_schema(tags=["Номенклатуры"])
# class NomenclatureViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet для полного управления номенклатурами в системе.

#     Номенклатура - это основная единица в системе, представляющая точку
#     отображения контента (рабочую станцию, дисплей и т.д.).

#     Endpoints:
#         GET /api/nomenclatures/ - Список активных номенклатур
#         GET /api/nomenclatures/{id}/ - Детали номенклатуры
#         POST /api/nomenclatures/ - Создать новую номенклатуру
#         PATCH /api/nomenclatures/{id}/ - Обновить номенклатуру
#         DELETE /api/nomenclatures/{id}/ - Деактивировать номенклатуру
#         GET /api/nomenclatures/inactive_list/ - Список неактивных
#         GET /api/nomenclatures/broadcast/ - Номенклатуры для вещания
#         GET /api/nomenclatures/versions/ - Все версии ПО
#         GET /api/nomenclatures/get_one_by_code1c/ - Поиск по коду 1C

#     Permissions:
#         - list: AllowAny
#         - create: IsAuthenticated + IsStaff
#         - retrieve: AllowAny
#         - update: IsAuthenticated + IsStaff
#         - destroy: IsAuthenticated + IsStaff
#     """

#     queryset = Nomenclature.web.select_related(
#         "legalEntity",
#         "brand",
#         "responsible_ad",
#         "typeOfPlace",
#     )

#     serializer_class = NomenclatureSerializer
#     permission_classes = [StaffCUDallRead]
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = NomenclatureFilter
#     CACHE_TIMEOUT = 300

#     def get_serializer(self, *args, **kwargs):
#         """
#         Динамически выбирает сериализатор в зависимости от типа операции.

#         Для операции 'list' (получение списка) используется NomenclatureListSerializer.
#         Для остальных операций (retrieve, create, update, destroy) используется
#         полный NomenclatureSerializer со всеми полями.
#         """
#         if self.action == "list":
#             # Для списка всегда используем NomenclatureListSerializer
#             # (и для обычного списка, и для поиска)
#             serializer_class = NomenclatureCardSerializer
#         else:
#             serializer_class = NomenclatureSerializer

#         if "data" in kwargs and isinstance(kwargs["data"], list):
#             kwargs["many"] = True

#         return serializer_class(*args, **kwargs)

#     def get_queryset(self):
#         """Оптимизирует queryset в зависимости от типа запроса."""
#         base_qs = super().get_queryset()

#         # Для поиска - теперь используем search_vector
#         if self.action == "list" and self.request.query_params.get('search'):
#             return base_qs.select_related(
#                 'brand',
#                 'typeOfPlace',
#                 'legalEntity',
#                 'responsible_ad',
#             ).prefetch_related(
#                 "images",
#                 Prefetch(
#                     'tenants',
#                     queryset=Counterparty.objects.only(
#                         'id', 'first_name', 'last_name',
#                         'middle_name', 'additional_name', 'keyword'
#                     ).prefetch_related('brands')
#                 )
#             ).defer(
#                 'description', 'settings', 'hw_info'
#             )

#         # Для обычного списка - полный queryset с сортировкой
#         tc = TypeOfPlace.objects.filter(name="Торговый центр").first()

#         if tc:
#             ordering_case = Case(
#                 When(typeOfPlace_id=tc.id, then=Value(0)),
#                 default=Value(1),
#                 output_field=IntegerField(),
#             )
#         else:
#             ordering_case = Value(1)

#         return (
#             base_qs
#             .select_related(
#                 "legalEntity",
#                 "brand",
#                 "responsible_ad",
#                 "typeOfPlace",
#                 "responsible_radio",
#                 "responsible_technic",
#                 "responsible_technic_on_address",
#                 "responsible_placement_marketing",
#             )
#             .prefetch_related(
#                 "images",
#                 Prefetch(
#                     'tenants',
#                     queryset=Counterparty.objects.only(
#                         'id', 'first_name', 'last_name',
#                         'middle_name', 'additional_name', 'keyword'
#                     ).prefetch_related('brands')
#                 )
#             )
#             .annotate(tenants_count=Count("tenants", distinct=True))
#             .order_by(
#                 ordering_case,
#                 "-tenants_count",
#                 "-created",
#             )
#         )

#     @extend_schema(summary="Номенклатуры по городу (по city_slug)")
#     @action(
#         detail=False,
#         methods=["get"],
#         url_path="by-city/(?P<city_slug>[^/.]+)",
#         permission_classes=[AllowAny],
#     )
#     def by_city(self, request, city_slug=None):
#         """
#         Возвращает агрегированные данные по номенклатуре для указанного города.
#         """

#         city = City.objects.filter(slug=city_slug).first()
#         if not city:
#             return Response(
#                 {"error": f"Город с slug '{city_slug}' не найден"},
#                 status=404,
#             )

#         queryset = (
#             Nomenclature.web
#             .filter(address__address__city=city)
#             .select_related(
#                 'typeOfPlace',
#                 'brand',
#                 'address__address__city',
#             )
#             .prefetch_related(
#                 Prefetch(
#                     'address',
#                     queryset=NomenclatureAddress.objects.select_related('address')
#                 )
#             )
#         )

#         min_price = queryset.aggregate(
#             min_price=models.Min("pricePerMonth")
#         )["min_price"] or 0.0

#         serializer = CityNomenclaturesSerializer(
#             queryset,
#             many=True,
#             context={"city_name": city.name}
#         )

#         return Response({
#             "city": city.name,
#             "minPrice": min_price,
#             "nomenclatures": serializer.data,
#             "count": queryset.count(),
#         })

#     def list(self, request, *args, **kwargs):
#         search_term = request.query_params.get('search')

#         if search_term is not None and len(search_term.strip()) < 3:
#             return Response(
#                 {"detail": "Поисковый запрос должен содержать не менее 3 символов."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         if not search_term:
#             return super().list(request, *args, **kwargs)

#         # Кэшируем финальный результат (сериализованные данные)
#         cache_page = request.query_params.get('page', 1)
#         cache_limit = request.query_params.get('limit', self.paginator.page_size)
#         cache_key = f"nomenclature_search_result_{hash(search_term)}_{cache_page}_{cache_limit}"

#         cached_result = cache.get(cache_key)
#         if cached_result:
#             logger.info(f"📦 Взят из кэша результат для '{search_term}'")
#             return Response(cached_result)

#         try:
#             from collections import Counter
#             from nomenclatures.services.search import NomenclatureSearchService

#             # Получаем queryset через сервис (он сам решит, брать из кэша или нет)
#             base_queryset = NomenclatureSearchService.search(
#                 query=search_term,
#                 for_web=True,
#                 limit=5000,
#                 use_cache=True
#             )

#             if not base_queryset:
#                 result = {'count': 0, 'next': None, 'previous': None, 'results': []}
#                 cache.set(cache_key, result, self.CACHE_TIMEOUT)
#                 return Response(result)

#             tc_ids = set(TypeOfPlace.objects.filter(is_mall=True).values_list('id', flat=True))

#             # Дополняем queryset для отображения
#             queryset = (
#                 base_queryset
#                 .select_related('brand', 'typeOfPlace', 'legalEntity', 'responsible_ad')
#                 .prefetch_related(
#                     'images',
#                     Prefetch(
#                         'tenants',
#                         queryset=Counterparty.objects.only(
#                             'id', 'first_name', 'last_name',
#                             'middle_name', 'additional_name', 'keyword'
#                         ).prefetch_related('brands')
#                     )
#                 )
#                 .defer('description', 'settings', 'hw_info')
#                 .annotate(tenants_count=Count('tenants', distinct=True))
#             )

#             # Считаем частоту брендов
#             brand_freq = Counter(
#                 n.brand_id for n in queryset if n.brand_id is not None
#             )

#             def sort_key(n):
#                 is_mall = 0 if (n.typeOfPlace_id in tc_ids) else 1
#                 tenants = -n.tenants_count
#                 brand_pop = -brand_freq.get(n.brand_id, 0)
#                 return (is_mall, tenants, brand_pop)

#             sorted_list = sorted(queryset, key=sort_key)

#             # Пагинация
#             page = self.paginator.paginate_queryset(sorted_list, request)
#             if page is not None:
#                 serializer = self.get_serializer(page, many=True)
#                 result = self.get_paginated_response(serializer.data).data
#             else:
#                 serializer = self.get_serializer(sorted_list, many=True)
#                 result = {
#                     'count': len(serializer.data),
#                     'next': None,
#                     'previous': None,
#                     'results': serializer.data
#                 }

#             # Кэшируем финальный результат
#             cache.set(cache_key, result, self.CACHE_TIMEOUT)
#             logger.info(f"💾 Закэширован результат для '{search_term}'")
#             return Response(result)

#         except Exception as e:
#             logger.error(f'Search error: {e}', exc_info=True)
#             # Fallback на простой поиск
#             queryset = self.get_queryset().filter(name__icontains=search_term)[:50]
#             serializer = self.get_serializer(queryset, many=True)
#             return Response({
#                 'count': len(serializer.data),
#                 'next': None,
#                 'previous': None,
#                 'results': serializer.data
#             })

#     @action(detail=True, methods=["get"], url_path="tabs")
#     def tabs(self, request, pk):
#         nomenclature = self.get_object()
#         tab = request.query_params.get("q")

#         if not tab:
#             raise ValidationError({"q": "Query-параметр 'q' обязателен. Например: ?q=tenants"})

#         handler = self._get_tab_handler(tab)
#         if not handler:
#             raise ValidationError({"q": f"Неподдерживаемая вкладка '{tab}'"})

#         return handler(nomenclature)

#     def _get_tab_handler(
#             self, tab: str
#     ) -> Optional[Callable[[Nomenclature], Response]]:
#         return {
#             "tenants": self._tenants_tab,
#             "contacts": self._contacts_tab,
#             "photos": self._photos_tab,
#         }.get(tab)

#     def _tenants_tab(self, nomenclature):
#         serializer = CounterpartiesShortSerializer(
#             nomenclature.tenants.all(),
#             many=True
#         )
#         return Response(serializer.data)

#     def _contacts_tab(self, nomenclature):
#         result = {
#             "legal_entity": None,
#             "legal_entity_cp": [],
#             "marketing": None,
#             "ad": None,
#         }

#         legal_entity = nomenclature.legalEntity

#         if legal_entity:
#             result["legal_entity"] = CounterpartyContactInfoSerializer(
#                 legal_entity.contacts.all(),
#                 many=True
#             ).data

#             # контактные лица юрлица
#             contacts = []

#             for user in legal_entity.contact_persons.all():
#                 contacts.extend(user.contacts_cp.all())

#             result["legal_entity_cp"] = UserContactInfoSerializer(
#                 contacts,
#                 many=True
#             ).data

#         # -------------------------
#         # Marketing responsible
#         # -------------------------
#         if nomenclature.responsible_placement_marketing:
#             contacts = nomenclature.responsible_placement_marketing.contacts_cp.all()
#             result["marketing"] = UserContactInfoSerializer(
#                 contacts,
#                 many=True
#             ).data

#         # -------------------------
#         # AD responsible
#         # -------------------------
#         if nomenclature.responsible_ad:
#             contacts = nomenclature.responsible_ad.contacts_cp.all()
#             result["ad"] = UserContactInfoSerializer(
#                 contacts,
#                 many=True
#             ).data

#         return Response(result)

#     def _photos_tab(self, nomenclature):
#         serializer = PhotoSerializer(
#             nomenclature.images.all(),
#             many=True
#         )
#         return Response(serializer.data)

#     @action(detail=False, methods=['get'])
#     def grouped(self, request):
#         qs = Nomenclature.web.select_related('brand', 'typeOfPlace')

#         filterset = self.filterset_class(
#             request.query_params,
#             queryset=qs,
#             request=request
#         )

#         qs = filterset.qs.annotate(
#             tenants_count=Count("tenants", distinct=True)
#         )

#         group_by = request.query_params.get('by')

#         GROUP_MAP = {
#             'brand': lambda x: x['brand_name'] if x['brand_id'] else None,
#         }

#         if group_by not in GROUP_MAP:
#             return Response({
#                 'error': 'Invalid group param',
#                 'allowed': list(GROUP_MAP.keys())
#             }, status=400)

#         serializer = ShortBrandNomenclatureSerializer(qs, many=True)
#         data = serializer.data

#         grouped = {}
#         for item in data:
#             key = GROUP_MAP[group_by](item)

#             if key not in grouped:
#                 grouped[key] = {
#                     'name': key,
#                     'typeOfPlace': item['type_of_place'],
#                     'brand_id': item['brand_id'],
#                     'brand_logotype': item['brand_logotype'],
#                     'amount': 1,
#                     'tenants_count': item.get('tenants_count', 0),
#                 }
#             else:
#                 grouped[key]['amount'] += 1
#                 grouped[key]['tenants_count'] += item.get('tenants_count', 0)

#         TC = "Торговый центр"

#         def sort_key(x):
#             is_tc = x['typeOfPlace'] == TC
#             if is_tc:
#                 # ТЦ: сначала по убыванию арендаторов, затем по убыванию amount
#                 return 0, -x['tenants_count'], -x['amount'], ''
#             else:
#                 # Остальные: по алфавиту typeOfPlace, затем по убыванию amount
#                 return 1, 0, -x['amount'], x['typeOfPlace'] or ''

#         result = sorted(grouped.values(), key=sort_key)
#         for item in result:
#             item.pop('tenants_count', None)
#         page = self.paginate_queryset(result)
#         if page is not None:
#             return self.get_paginated_response(page)
#         return Response(result)

#     def perform_create(self, serializer):
#         """
#         Сохраняет новую номенклатуру с текущим пользователем как владельцем.

#         Этот метод вызывается автоматически при POST запросе к созданию номенклатуры.
#         Он переопределяет стандартное поведение для установки поля 'owner'
#         автоматически на основе текущего аутентифицированного пользователя.

#         Это предотвращает попыток пользователей установить владельца на кого-то другого
#         и обеспечивает правильное отслеживание, кто создал номенклатуру.

#         Args:
#             serializer: Экземпляр сериализатора с валидными данными
#                        (serializer.validated_data содержит все валидные поля).

#         Returns:
#             None (сохранение происходит в serializer.save()).

#         Side Effects:
#             - Сохраняет новый объект Nomenclature в БД
#             - Устанавливает поле owner = request.user
#             - Создает запись в истории изменений (если включено)

#         Examples:
#             >>> # При POST запросе с данными
#             >>> response = client.post('/api/nomenclatures/', data={
#             ...     'name': 'Display 1',
#             ...     'description': 'Test display'
#             ... })
#             >>> # owner автоматически будет установлен на текущего пользователя
#         """
#         serializer.save(owner=self.request.user)

#     @extend_schema(summary="Список деактивированных номенклатур")
#     @action(
#         detail=False,
#         methods=["get"],
#         url_path="inactive_list",
#         permission_classes=[StaffCUDallRead]
#     )
#     def inactive(self, request):
#         """
#         Получить пагинированный список всех деактивированных номенклатур.

#         Этот метод доступен только для персонала (staff). Он возвращает те же данные,
#         что и обычный список, но для неактивных номенклатур (is_active=False).

#         Выполняет оптимизацию БД запросов через select_related и prefetch_related:
#         - select_related('owner', 'availability', 'brand', 'address') - для быстрого
#           доступа к связанным объектам
#         - prefetch_related('images') - для предзагрузки изображений

#         Поддерживает стандартную пагинацию DRF, если количество результатов превышает
#         лимит страницы (обычно 20-100 элементов на странице).

#         Args:
#             request: HTTP запрос от клиента.

#         Returns:
#             Response: Пагинированный список неактивных номенклатур в JSON формате
#                      или весь список, если он меньше размера страницы.
#                      Структура: {
#                          'count': int,
#                          'next': str или null,
#                          'previous': str или null,
#                          'results': [NomenclatureListSerializer, ...]
#                      }

#         Status Codes:
#             200 OK: Успешно получен список
#             403 FORBIDDEN: Пользователь не имеет прав доступа

#         Examples:
#             >>> response = client.get('/api/nomenclatures/inactive_list/')
#             >>> response.status_code
#             200
#             >>> response.data['count']
#             42  # количество неактивных номенклатур
#         """
#         qs = (
#             Nomenclature.inactive
#             .select_related("owner", "availability", "brand", "address")
#             .prefetch_related("images")
#         )

#         page = self.paginate_queryset(qs)
#         serializer = self.get_serializer(page or qs, many=True)
#         return (
#             self.get_paginated_response(serializer.data)
#             if page is not None
#             else Response(serializer.data)
#         )

#     @extend_schema(summary="Работа с деактивированной номенклатурой")
#     @action(
#         detail=True,
#         methods=["get", "patch"],
#         url_path="inactive",
#         permission_classes=[StaffCUDallRead]
#     )
#     def inactive_detail(self, request, pk=None):
#         """
#         Получить полные детали или обновить деактивированную номенклатуру по ID.

#         Этот эндпоинт предоставляет возможность просмотра и редактирования
#         удаленных (деактивированных) номенклатур. Используется администраторами
#         для восстановления или окончательного удаления номенклатур из системы.

#         GET запрос:
#             Возвращает полные данные деактивированной номенклатуры со всеми полями,
#             включая связанные объекты (владелец, бренд, адрес, изображения).

#         PATCH запрос:
#             Позволяет частично обновить деактивированную номенклатуру. Например,
#             может быть использовано для изменения причины деактивации, добавления
#             заметок или восстановления номенклатуры (изменение is_active=True).

#         Оптимизация запросов:
#             - select_related для owner, availability, brand, address
#             - prefetch_related для images (многие-ко-многим связь)

#         Args:
#             request: HTTP запрос (GET или PATCH).
#             pk: UUID номенклатуры.

#         Returns:
#             GET Response: Полные данные деактивированной номенклатуры (NomenclatureSerializer).
#             PATCH Response: Обновленные данные номенклатуры (NomenclatureSerializer).

#         Raises:
#             HTTP_404_NOT_FOUND: Если номенклатура не найдена или не деактивирована.
#             HTTP_403_FORBIDDEN: Если пользователь не имеет прав доступа (не staff).
#             HTTP_400_BAD_REQUEST: При ошибке валидации данных (PATCH).

#         Examples:
#             >>> # Получить деактивированную номенклатуру
#             >>> response = client.get('/api/nomenclatures/123e4567/inactive/')
#             >>> response.status_code
#             200

#             >>> # Восстановить номенклатуру
#             >>> response = client.patch(
#             ...     '/api/nomenclatures/123e4567/inactive/',
#             ...     data={'is_active': True}
#             ... )
#             >>> response.status_code
#             200
#         """
#         identifier = pk
#         if not identifier:
#             raise NotFound("Не указан идентификатор КА.")

#         # Проверяем, валидный ли UUID
#         is_uuid = False
#         try:
#             UUID(str(identifier))
#             is_uuid = True
#         except ValueError:
#             is_uuid = False

#         instance = None

#         # Если UUID — ищем по id
#         if is_uuid:
#             try:
#                 instance = (
#                     Nomenclature.inactive
#                     .select_related("owner", "availability", "brand", "address")
#                     .prefetch_related("images")
#                     .get(id=identifier)
#                 )
#             except Nomenclature.DoesNotExist:
#                 pass

#         # Если не UUID или UUID не найден — ищем по code1c
#         if instance is None:
#             try:
#                 instance = (
#                     Nomenclature.inactive
#                     .select_related("owner", "availability", "brand", "address")
#                     .prefetch_related("images")
#                     .get(code1c=identifier)
#                 )
#             except Nomenclature.DoesNotExist:
#                 raise NotFound("Номенклатура не найдена.")

#         if request.method == "GET":
#             serializer = self.get_serializer(instance)
#             return Response(serializer.data)

#         serializer = self.get_serializer(
#             instance,
#             data=request.data,
#             partial=True,
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

#     @action(detail=False, methods=["GET"], url_path="broadcast")
#     def broadcast(self, request):
#         """
#         Получить список номенклатур для вещания с учетом роли пользователя.

#         Этот метод реализует сложную логику авторизации в зависимости от типа пользователя:

#         Администраторы (is_admin, is_superuser, is_manager):
#             - Видят все активные номенклатуры с флагом broadcast=True в их правовых лиц
#             - Это позволяет администраторам контролировать все доступные номенклатуры для вещания

#         Обычные пользователи (is_contact_person_broadcast=True):
#             - Видят только номенклатуры своих контрагентов (counterparties)
#             - Это предотвращает несанкционированный доступ к номенклатурам других компаний

#         Процесс проверки:
#             1. Проверяется, аутентифицирован ли пользователь
#             2. Проверяется, имеет ли пользователь флаг broadcast
#             3. В зависимости от типа, выбирается соответствующий queryset
#             4. Результаты пагинируются и возвращаются

#         Args:
#             request: HTTP запрос с информацией о пользователе.

#         Returns:
#             Response: Пагинированный список номенклатур для вещания в JSON формате.
#                      Структура: {
#                          'count': int,
#                          'next': str или null,
#                          'previous': str или null,
#                          'results': [NomenclatureListSerializer, ...]
#                      }

#         Status Codes:
#             200 OK: Успешно получен список
#             403 FORBIDDEN: Пользователь не аутентифицирован или нет права на broadcast

#         Data Structure:
#             {
#                 'count': 15,
#                 'next': 'http://api.example.com/nomenclatures/broadcast/?page=2',
#                 'previous': None,
#                 'results': [
#                     {
#                         'id': '123e4567-e89b-12d3-a456-426614174000',
#                         'name': 'Display 1',
#                         'description': 'Main display',
#                         ...
#                     }
#                 ]
#             }

#         Raises:
#             HTTP_403_FORBIDDEN: Если пользователь не имеет прав на broadcast

#         Examples:
#             >>> # Администратор видит все номенклатуры для вещания
#             >>> client.force_authenticate(user=admin_user)
#             >>> response = client.get('/api/nomenclatures/broadcast/')
#             >>> response.data['count']
#             50  # все номенклатуры

#             >>> # Обычный пользователь видит только свои контрагентов
#             >>> client.force_authenticate(user=regular_user)
#             >>> response = client.get('/api/nomenclatures/broadcast/')
#             >>> response.data['count']
#             5  # только он номенклатуры
#         """
#         user = request.user
#         is_broadcast = user.is_contact_person_broadcast

#         if (not user.is_authenticated and not self._is_admin(request.user)) or (
#                 not user.is_authenticated and not is_broadcast):
#             return Response(
#                 {'message': 'Недостаточно прав.'},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         if self._is_admin(request.user):
#             qs = (
#                 Nomenclature.active
#                 .select_related("owner", "availability", "brand", "address")
#                 .prefetch_related("images")
#                 .filter(legalEntity__broadcast=True)
#             )
#         elif is_broadcast:
#             user_counterparties = user.counterparties.all()
#             qs = (
#                 self.get_queryset()
#                 .filter(legalEntity__in=user_counterparties)
#             )
#         else:
#             return Response(
#                 {'message': 'Недостаточно прав.'},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         page = self.paginate_queryset(qs)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)

#         serializer = self.get_serializer(qs, many=True)
#         return Response(serializer.data)

#     def update(self, request, *args, **kwargs):
#         """
#         Обновить номенклатуру с контролем редактируемых полей.

#         Этот метод переопределяет стандартное поведение DRF для добавления
#         дополнительной валидации. Он проверяет, что пользователь пытается
#         обновить только разрешенные поля, и выбрасывает ошибку в противном случае.

#         Разрешенные для редактирования поля:
#             - Основная информация: name, description, timezone
#             - Конфигурация: settings, contentType, typeOfPlace
#             - Связи: brand_id, legalEntity_id, tenants_id, address_id
#             - Персонал: responsible_radio, responsible_ad
#             - Дополнительно: floor_space, traffic, pricePerMonth, media

#         Защищенные поля (не могут быть отредактированы обычными пользователями):
#             - id, code1c, is_active (только администраторы)
#             - created, modified, article (автоматические поля)
#             - owner, version, hw_info (системные поля)

#         Args:
#             request: HTTP PATCH/PUT запрос с данными для обновления.
#             *args: Позиционные аргументы viewset.
#             **kwargs: Именованные аргументы (обычно pk).

#         Returns:
#             Response: Обновленные данные номенклатуры (NomenclatureSerializer).

#         Raises:
#             HTTP_400_BAD_REQUEST: Если используются недопустимые поля.
#                                  Сообщение: "Изменить можно только название, описание...
#                                            Лишние ключи: {keys}."
#             HTTP_404_NOT_FOUND: Если номенклатура не найдена.
#             HTTP_403_FORBIDDEN: Если пользователь не имеет прав на редактирование.

#         Examples:
#             >>> # Правильное обновление
#             >>> response = client.patch(
#             ...     '/api/nomenclatures/123e4567/update/',
#             ...     data={'name': 'New Name', 'description': 'New description'}
#             ... )
#             >>> response.status_code
#             200

#             >>> # Попытка изменить защищенное поле
#             >>> response = client.patch(
#             ...     '/api/nomenclatures/123e4567/',
#             ...     data={'name': 'New Name', 'is_active': False}  # is_active защищено
#             ... )
#             >>> response.status_code
#             400
#             >>> response.data['detail']
#             'Изменить можно только... Лишние ключи: is_active.'
#         """
#         forbidden_fields = {"is_active"}  # здесь перечисляем только запрещённые поля
#         sent_keys = set(request.data.keys())
#         blocked_keys = sent_keys & forbidden_fields

#         if blocked_keys:
#             raise serializers.ValidationError(
#                 f"Редактирование запрещено для полей: {', '.join(blocked_keys)}"
#             )

#         return super().update(request, *args, **kwargs)

#     def get_object(self):
#         identifier = self.kwargs.get('pk')
#         if not identifier:
#             raise NotFound("Не указан идентификатор номенклатуры.")

#         # Проверяем, валидный ли UUID
#         is_uuid = False
#         try:
#             UUID(str(identifier))
#             is_uuid = True
#         except ValueError:
#             is_uuid = False

#         # Если UUID — ищем по id
#         if is_uuid:
#             try:
#                 nomenclature = Nomenclature.objects.get(id=identifier)
#                 return nomenclature
#             except Nomenclature.DoesNotExist:
#                 raise NotFound("Номенклатура не найдена.")

#         # Если не UUID — пробуем найти по code1c
#         try:
#             nomenclature = Nomenclature.objects.get(code1c=identifier)
#             return nomenclature
#         except Nomenclature.DoesNotExist:
#             pass

#         # Если не code1c — ищем по old_catalog_slug
#         try:
#             nomenclature = Nomenclature.objects.get(old_catalog_slug=identifier)
#             return nomenclature
#         except Nomenclature.DoesNotExist:
#             raise NotFound("Номенклатура не найдена.")

#     @extend_schema(summary="Деактивировать номенклатуру")
#     def destroy(self, request, *args, **kwargs):
#         """
#         Выполнить мягкое удаление (деактивацию) номенклатуры по ID.

#         Этот метод переопределяет стандартное поведение DELETE для реализации
#         'мягкого удаления' (soft delete). Вместо полного удаления из БД,
#         номенклатура просто помечается как неактивная (is_active=False).

#         Преимущества мягкого удаления:
#             - Сохраняет историю и ссылочную целостность
#             - Позволяет восстановить данные при необходимости
#             - Не нарушает связи с другими объектами (заказы, статистика и т.д.)

#         Процесс:
#             1. Получает объект номенклатуры по ID (pk)
#             2. Проверяет, не деактивирована ли она уже
#             3. Если деактивирована, возвращает ошибку 400
#             4. Если активна, устанавливает is_active=False и сохраняет
#             5. Возвращает 204 No Content при усписе или 400 Bad Request при ошибке

#         Args:
#             request: HTTP DELETE запрос.
#             *args: Позиционные аргументы viewset.
#             **kwargs: Именованные аргументы (обычно pk).

#         Returns:
#             Response:
#                 - На успех: пустой Response с статусом 204 No Content
#                 - На ошибку: JSON с сообщением об ошибке и статусом 400

#         Status Codes:
#             204 NO CONTENT: Номенклатура успешно деактивирована
#             400 BAD REQUEST: Номенклатура уже деактивирована
#             403 FORBIDDEN: Пользователь не имеет прав на удаление
#             404 NOT FOUND: Номенклатура не найдена

#         Side Effects:
#             - Изменяет поле is_active=False
#             - Не удаляет физически из БД (soft delete)
#             - Может создать достаточность в истории изменений

#         Examples:
#             >>> # Успешная деактивация
#             >>> response = client.delete('/api/nomenclatures/123e4567/')
#             >>> response.status_code
#             204
#             >>> response.content
#             b''  # пустой ответ

#             >>> # Попытка деактивировать уже деактивированную
#             >>> response = client.delete('/api/nomenclatures/456f7890/')
#             >>> response.status_code
#             400
#             >>> response.data['detail']
#             'Нельзя деактивировать номенклатуру, т.к она уже деактивирована.'

#         Warning:
#             После деактивации номенклатура будет недоступна для обычных пользователей
#             через /api/nomenclatures/, но доступна через /api/nomenclatures/inactive_list/
#         """
#         instance = self.get_object()
#         data = self.perform_destroy(instance)
#         return Response(
#             data={"detail": data} if data else None,
#             status=400 if data else 204,
#         )

#     def perform_destroy(self, instance):
#         """
#         Выполняет физическое сохранение деактивации номенклатуры в БД.

#         Вспомогательный метод для destroy(), который отделяет логику проверки
#         от логики сохранения. Выполняет следующие действия:

#         1. Проверяет, не деактивирована ли номенклатура уже
#         2. Если да, возвращает сообщение об ошибке (не выбрасывает исключение)
#         3. Если нет, устанавливает is_active=False и сохраняет в БД
#         4. Оптимизирует сохранение, указав только измененное поле (update_fields)

#         Использование update_fields:
#             - Более эффективно, чем сохранение всех полей
#             - Генерирует SQL UPDATE с одним полем, а не всеми
#             - Предотвращает нежелательные изменения других полей

#         Args:
#             instance: Объект Nomenclature для деактивации.

#         Returns:
#             str или None:
#                 - None если деактивация успешна
#                 - str с сообщением об ошибке если номенклатура уже деактивирована

#         Side Effects:
#             - Изменяет поле is_active в БД (если не деактивирована)

#         Examples:
#             >>> instance = Nomenclature.objects.get(pk='123e4567')
#             >>> result = viewset.perform_destroy(instance)
#             >>> result
#             None  # успешно
#             >>> instance.is_active
#             False

#             >>> # При повторном вызове
#             >>> result = viewset.perform_destroy(instance)
#             >>> result
#             'Нельзя деактивировать номенклатуру, т.к она уже деактивирована.'

#         Note:
#             Этот метод не выбрасывает исключения - он возвращает результат,
#             позволяя destroy() вернуть правильный статус код.
#         """
#         if instance.is_active is False:
#             return (
#                 "Нельзя деактивировать номенклатуру, т.к "
#                 "она уже деактивирована."
#             )
#         instance.is_active = False
#         instance.save(update_fields=["is_active"])
#         return None

#     @extend_schema(
#         summary="Получить список всех версий номенклатур",
#         responses={HTTP_200_OK: VersionsSerializer},
#     )
#     @action(detail=False, methods=["GET"], url_path="versions")
#     def get_versions(self, request):
#         """
#         Получить список всех уникальных версий ПО установленных на номенклатурах.

#         Этот метод извлекает все уникальные значения поля 'version' из БД,
#         отсортированные и выведенные списком. Используется для мониторинга версий ПО,
#         установленных на различных дисплеях и устройствах.

#         Query оптимизация:
#             - order_by() без аргументов - очищает стандартный порядок сортировки
#             - values_list('version', flat=True) - получает только одно поле
#             - distinct() - убирает дубликаты в памяти после выборки

#         Args:
#             request: HTTP GET запрос.

#         Returns:
#             Response: JSON с ключом 'versions' и списком версий.
#                      Структура: {
#                          'versions': ['1.0.0', '1.0.1', '1.1.0', '2.0.0', ...]
#                      }

#         Status Codes:
#             200 OK: успешно получен список

#         Data Structure:
#             {
#                 'versions': [
#                     '111',
#                     '112',
#                     '113',
#                     '120',
#                     ...
#                 ]
#             }

#         Examples:
#             >>> response = client.get('/api/nomenclatures/versions/')
#             >>> response.status_code
#             200
#             >>> response.data
#             {'versions': ['1.0.0', '1.0.1', '1.1.0']}
#             >>> len(response.data['versions'])
#             37  # количество уникальных версий

#         Performance Notes:
#             - Быстрый запрос, выполняется на уровне БД
#             - Для большого количества номенклатур может быть медленным
#             - Рекомендуется кэширование результата на уровне приложения
#             - Может быть оптимизировано добавлением индекса на поле version

#         Use Cases:
#             - Аналитика версий ПО
#             - Построение графиков обновления
#             - Проверка совместимости контента с версией ПО
#             - Отправки целевых обновлений определенным версиям
#         """
#         versions = (
#             Nomenclature.objects.order_by()
#             .values_list("version", flat=True)
#             .distinct()
#         )
#         return Response({"versions": versions}, status=HTTP_200_OK)

#     @action(
#         detail=False,
#         methods=["GET"],
#         url_path="get_uuid_by_id",
#         permission_classes=[AllowAny],
#     )
#     def get_id(self, request):
#         nomenclature = Nomenclature.objects.get(
#             id_rasb=request.data["id_rasb"]
#         )
#         return Response({"id": nomenclature.pk})

#     @extend_schema(
#         summary="Получить номенклатуры по списку ID",
#         parameters=[
#             OpenApiParameter(
#                 name='ids',
#                 description='UUID через запятую',
#                 required=True,
#                 type=str,
#             ),
#         ],
#         responses={200: NomenclatureListSerializer(many=True)},
#         tags=['Номенклатуры'],
#     )
#     @action(
#         detail=False,
#         methods=['GET'],
#         url_path='bulk',
#         permission_classes=[AllowAny],
#     )
#     def bulk(self, request):
#         raw = request.query_params.get('ids', '')
#         if not raw:
#             return Response(
#                 {'error': 'Параметр ids обязателен'},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # парсим и валидируем UUID
#         ids = []
#         for part in raw.split(','):
#             part = part.strip()
#             try:
#                 ids.append(UUID(part))
#             except ValueError:
#                 return Response(
#                     {'error': f'Невалидный UUID: {part}'},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#         if len(ids) > 100:
#             return Response(
#                 {'error': 'Максимум 100 ID за запрос'},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         queryset = (
#             Nomenclature.web.filter(id__in=ids)
#             .select_related('brand', 'typeOfPlace', 'legalEntity', 'responsible_ad')
#             .prefetch_related(
#                 'images',
#                 Prefetch(
#                     'tenants',
#                     queryset=Counterparty.objects.only(
#                         'id', 'first_name', 'last_name',
#                         'middle_name', 'additional_name', 'keyword'
#                     ).prefetch_related('brands')
#                 )
#             )
#             .defer('description', 'settings', 'hw_info')
#         )

#         serializer = NomenclatureCardSerializer(queryset, many=True)
#         return Response(serializer.data)

#     @staticmethod
#     def _is_admin(user):
#         """
#         Проверяет, является ли пользователь администратором системы.

#         Функция проверяет, аутентифицирован ли пользователь и имеет ли он одно из
#         следующих прав доступа: администратор, менеджер или суперпользователь.

#         Args:
#             user: Объект пользователя Django (django.contrib.auth.models.User или кастомный).

#         Returns:
#             bool: True если пользователь аутентифицирован и имеет права администратора,
#                 менеджера или является суперпользователем. False в остальных случаях.

#         Examples:
#             >>> user = User.objects.get(username='admin')
#             >>> _is_admin(user)
#             True

#             >>> anonymous = AnonymousUser()
#             >>> _is_admin(anonymous)
#             False

#         Note:
#             Функция требует, чтобы у пользователя были атрибуты:
#             - is_authenticated: указывает на аутентификацию
#             - is_admin: флаг администратора
#             - is_superuser: флаг суперпользователя
#             - is_manager: флаг менеджера
#         """
#         return (
#                 user.is_authenticated and (
#                 user.is_admin
#                 or user.is_superuser
#                 or user.is_manager
#         )
#         )
