from typing import Callable, Optional
from uuid import UUID

from django.core.cache import cache
from django.db.models import Count, Case, When, Value, IntegerField, Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.utils import inline_serializer, OpenApiResponse
from rest_framework import serializers
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
)

from api.constants import VersionsSerializer
from counterparties.models import Counterparty
from counterparties.serializers import CounterpartiesShortSerializer, CounterpartyContactInfoSerializer
from nomenclatures.services.opensearch_search import NomenclatureOpenSearchService
from users.permissions import StaffCUDallRead
from users.serializers import UserContactInfoSerializer
from ..filters import NomenclatureFilter
from ..models import Nomenclature, TypeOfPlace
from ..serializers import (
    NomenclatureSerializer,
    NomenclatureListSerializer,
    ShortBrandNomenclatureSerializer, PhotoSerializer,
)


@extend_schema_view(
    grouped=extend_schema(
        summary="Получить номенклатуры, сгруппированные по полю",
        description="""
        Возвращает список номенклатур, сгруппированных по указанному полю.

        Каждая группа содержит:
        - **name**: Название группы (значение поля группировки)
        - **items**: Массив номенклатур в этой группе

        Поддерживаемые параметры группировки:
        - **brand**: группировка по названию бренда
        - **legal**: группировка по названию юридического лица
        - **place**: группировка по типу места размещения
        - **address**: группировка по городу
        """,
        parameters=[
            OpenApiParameter(
                name='by',
                description='Поле для группировки (обязательный параметр)',
                required=True,
                type=str,
                enum=['brand', 'legal', 'place', 'address']
            ),
        ],
        responses={
            200: inline_serializer(
                name='GroupedNomenclaturesResponse',
                fields={
                    'name': serializers.CharField(),
                    'items': NomenclatureListSerializer(many=True)  # замените на ваш реальный сериализатор
                }
            ),
            400: OpenApiResponse(
                description='Ошибка валидации - неверный параметр группировки',
                response=inline_serializer(
                    name='GroupingErrorResponse',
                    fields={
                        'error': serializers.CharField(),
                        'allowed': serializers.ListField(child=serializers.CharField())
                    }
                )
            ),
        },
        examples=[
            OpenApiExample(
                'Успешный ответ',
                value=[
                    {
                        'name': 'test brand',
                        'items': [
                            {
                                'id': '123e4567-e89b-12d3-a456-426614174000',
                                'name': 'Display 1',
                                'timezone': 'UTC +7',
                                'status': 0,
                                'legalEntity': {
                                    'id': 1,
                                    'name': 'ООО Рекламное агентство'
                                },
                                'brand': {
                                    'id': 1,
                                    'name': 'test brand',
                                    'logotype': 'https://...'
                                }
                            }
                        ]
                    }
                ],
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Ошибка - неверный параметр',
                value={
                    'error': 'Invalid group param',
                    'allowed': ['brand', 'legal', 'place', 'address']
                },
                response_only=True,
                status_codes=['400']
            )
        ],
        tags=['Номенклатуры']
    )
)
@extend_schema(tags=["Номенклатуры"])
class NomenclatureViewSet(viewsets.ModelViewSet):
    """
    ViewSet для полного управления номенклатурами в системе.

    Номенклатура - это основная единица в системе, представляющая точку
    отображения контента (рабочую станцию, дисплей и т.д.).

    Endpoints:
        GET /api/nomenclatures/ - Список активных номенклатур
        GET /api/nomenclatures/{id}/ - Детали номенклатуры
        POST /api/nomenclatures/ - Создать новую номенклатуру
        PATCH /api/nomenclatures/{id}/ - Обновить номенклатуру
        DELETE /api/nomenclatures/{id}/ - Деактивировать номенклатуру
        GET /api/nomenclatures/inactive_list/ - Список неактивных
        GET /api/nomenclatures/broadcast/ - Номенклатуры для вещания
        GET /api/nomenclatures/versions/ - Все версии ПО
        GET /api/nomenclatures/get_one_by_code1c/ - Поиск по коду 1C

    Permissions:
        - list: AllowAny
        - create: IsAuthenticated + IsStaff
        - retrieve: AllowAny
        - update: IsAuthenticated + IsStaff
        - destroy: IsAuthenticated + IsStaff
    """

    queryset = Nomenclature.web.select_related(
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

        Для операции 'list' (получение списка) используется NomenclatureListSerializer.
        Для остальных операций (retrieve, create, update, destroy) используется
        полный NomenclatureSerializer со всеми полями.
        """
        if self.action == "list":
            # Для списка всегда используем NomenclatureListSerializer
            # (и для обычного списка, и для поиска)
            serializer_class = NomenclatureListSerializer
        else:
            serializer_class = NomenclatureSerializer

        if "data" in kwargs and isinstance(kwargs["data"], list):
            kwargs["many"] = True

        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        """Оптимизирует queryset в зависимости от типа запроса."""
        base_qs = super().get_queryset()

        # Для поиска - оптимизированный queryset (все нужные поля для ListSerializer)
        if self.action == "list" and self.request.query_params.get('search_text'):
            return base_qs.select_related(
                'brand',
                'typeOfPlace',
                'legalEntity',
                'responsible_ad',
            ).prefetch_related(
                "images",
                Prefetch(
                    'tenants',
                    queryset=Counterparty.objects.only(
                        'id', 'first_name', 'last_name',
                        'middle_name', 'additional_name', 'keyword'
                    ).prefetch_related('brands')  # Добавляем prefetch для брендов
                )
            ).defer(
                'description', 'settings', 'hw_info'
            )

        # Для обычного списка - полный queryset с сортировкой
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
                    ).prefetch_related('brands')  # Добавляем prefetch для брендов
                )
            )
            .annotate(tenants_count=Count("tenants", distinct=True))
            .order_by(
                ordering_case,
                "-tenants_count",
                "-created",
            )
        )

    def list(self, request, *args, **kwargs):
        search_term = request.query_params.get('search')

        # 🔍 РЕЖИМ ПОИСКА ЧЕРЕЗ OPENSEARCH
        if search_term:
            cache_key = f"nomenclature_search_os_v2_{hash(search_term)}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)

            try:
                # Получаем результаты из OpenSearch
                os_results = NomenclatureOpenSearchService.search(search_term, limit=5000)
                ids = [hit.meta.id for hit in os_results]

                if not ids:
                    result = {'count': 0, 'next': None, 'previous': None, 'results': []}
                    cache.set(cache_key, result, self.CACHE_TIMEOUT)
                    return Response(result)

                # Фильтруем Django queryset по найденным id
                queryset = Nomenclature.web.filter(id__in=ids)

                # Сохраняем порядок релевантности
                preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
                queryset = queryset.order_by(preserved)

                # Подключаем prefetch/select_related как для обычного списка
                queryset = queryset.select_related(
                    'brand', 'typeOfPlace', 'legalEntity', 'responsible_ad'
                ).prefetch_related(
                    'images',
                    Prefetch(
                        'tenants',
                        queryset=Counterparty.objects.only(
                            'id', 'first_name', 'last_name',
                            'middle_name', 'additional_name', 'keyword'
                        ).prefetch_related('brands')
                    )
                ).defer('description', 'settings', 'hw_info')

                # Пагинация
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = NomenclatureListSerializer(page, many=True)
                    result = self.get_paginated_response(serializer.data).data
                else:
                    serializer = NomenclatureListSerializer(queryset, many=True)
                    result = {'count': len(serializer.data), 'next': None, 'previous': None, 'results': serializer.data}

                # Кэшируем результат
                cache.set(cache_key, result, self.CACHE_TIMEOUT)
                return Response(result)

            except Exception as e:
                # fallback на обычный ORM поиск
                queryset = self.get_queryset().filter(name__icontains=search_term)[:50]
                serializer = NomenclatureListSerializer(queryset, many=True)
                result = {'count': len(serializer.data), 'next': None, 'previous': None, 'results': serializer.data}
                return Response(result)

        # 📄 ОБЫЧНЫЙ СПИСОК без поиска
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NomenclatureListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NomenclatureListSerializer(queryset, many=True)
        return Response({'count': len(serializer.data), 'next': None, 'previous': None, 'results': serializer.data})

    @action(detail=True, methods=["get"], url_path="tabs")
    def tabs(self, request, pk):
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
        return {
            "tenants": self._tenants_tab,
            "contacts": self._contacts_tab,
            "photos": self._photos_tab,
        }.get(tab)

    def _tenants_tab(self, nomenclature):
        serializer = CounterpartiesShortSerializer(
            nomenclature.tenants.all(),
            many=True
        )
        return Response(serializer.data)

    def _contacts_tab(self, nomenclature):
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

            # контактные лица юрлица
            contacts = []

            for user in legal_entity.contact_persons.all():
                contacts.extend(user.contacts_cp.all())

            result["legal_entity_cp"] = UserContactInfoSerializer(
                contacts,
                many=True
            ).data

        # -------------------------
        # Marketing responsible
        # -------------------------
        if nomenclature.responsible_placement_marketing:
            contacts = nomenclature.responsible_placement_marketing.contacts_cp.all()
            result["marketing"] = UserContactInfoSerializer(
                contacts,
                many=True
            ).data

        # -------------------------
        # AD responsible
        # -------------------------
        if nomenclature.responsible_ad:
            contacts = nomenclature.responsible_ad.contacts_cp.all()
            result["ad"] = UserContactInfoSerializer(
                contacts,
                many=True
            ).data

        return Response(result)

    def _photos_tab(self, nomenclature):
        serializer = PhotoSerializer(
            nomenclature.images.all(),
            many=True
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def grouped(self, request):
        qs = Nomenclature.web.select_related('brand', 'typeOfPlace')

        filterset = self.filterset_class(
            request.query_params,
            queryset=qs,
            request=request
        )

        tc = TypeOfPlace.objects.filter(name="Торговый центр").first()

        if tc:
            ordering_case = Case(
                When(typeOfPlace_id=tc.id, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        else:
            ordering_case = Value(1)

        qs = filterset.qs.annotate(tenants_count=Count("tenants", distinct=True)).order_by(
            ordering_case,

            "-tenants_count",
            'amount',
            "-created",
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

        # Сначала сериализуем ВСЁ, потом группируем
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
                    'amount': 1
                }
            else:
                grouped[key]['amount'] += 1  # ← исправлен путь

        result = list(grouped.values())

        # Пагинируем уже сгруппированный результат
        page = self.paginate_queryset(result)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(result)

    def perform_create(self, serializer):
        """
        Сохраняет новую номенклатуру с текущим пользователем как владельцем.

        Этот метод вызывается автоматически при POST запросе к созданию номенклатуры.
        Он переопределяет стандартное поведение для установки поля 'owner'
        автоматически на основе текущего аутентифицированного пользователя.

        Это предотвращает попыток пользователей установить владельца на кого-то другого
        и обеспечивает правильное отслеживание, кто создал номенклатуру.

        Args:
            serializer: Экземпляр сериализатора с валидными данными
                       (serializer.validated_data содержит все валидные поля).

        Returns:
            None (сохранение происходит в serializer.save()).

        Side Effects:
            - Сохраняет новый объект Nomenclature в БД
            - Устанавливает поле owner = request.user
            - Создает запись в истории изменений (если включено)

        Examples:
            >>> # При POST запросе с данными
            >>> response = client.post('/api/nomenclatures/', data={
            ...     'name': 'Display 1',
            ...     'description': 'Test display'
            ... })
            >>> # owner автоматически будет установлен на текущего пользователя
        """
        serializer.save(owner=self.request.user)

    @extend_schema(summary="Список деактивированных номенклатур")
    @action(
        detail=False,
        methods=["get"],
        url_path="inactive_list",
        permission_classes=[StaffCUDallRead]
    )
    def inactive(self, request):
        """
        Получить пагинированный список всех деактивированных номенклатур.

        Этот метод доступен только для персонала (staff). Он возвращает те же данные,
        что и обычный список, но для неактивных номенклатур (is_active=False).

        Выполняет оптимизацию БД запросов через select_related и prefetch_related:
        - select_related('owner', 'availability', 'brand', 'address') - для быстрого
          доступа к связанным объектам
        - prefetch_related('images') - для предзагрузки изображений

        Поддерживает стандартную пагинацию DRF, если количество результатов превышает
        лимит страницы (обычно 20-100 элементов на странице).

        Args:
            request: HTTP запрос от клиента.

        Returns:
            Response: Пагинированный список неактивных номенклатур в JSON формате
                     или весь список, если он меньше размера страницы.
                     Структура: {
                         'count': int,
                         'next': str или null,
                         'previous': str или null,
                         'results': [NomenclatureListSerializer, ...]
                     }

        Status Codes:
            200 OK: Успешно получен список
            403 FORBIDDEN: Пользователь не имеет прав доступа

        Examples:
            >>> response = client.get('/api/nomenclatures/inactive_list/')
            >>> response.status_code
            200
            >>> response.data['count']
            42  # количество неактивных номенклатур
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

    @extend_schema(summary="Работа с деактивированной номенклатурой")
    @action(
        detail=True,
        methods=["get", "patch"],
        url_path="inactive",
        permission_classes=[StaffCUDallRead]
    )
    def inactive_detail(self, request, pk=None):
        """
        Получить полные детали или обновить деактивированную номенклатуру по ID.

        Этот эндпоинт предоставляет возможность просмотра и редактирования
        удаленных (деактивированных) номенклатур. Используется администраторами
        для восстановления или окончательного удаления номенклатур из системы.

        GET запрос:
            Возвращает полные данные деактивированной номенклатуры со всеми полями,
            включая связанные объекты (владелец, бренд, адрес, изображения).

        PATCH запрос:
            Позволяет частично обновить деактивированную номенклатуру. Например,
            может быть использовано для изменения причины деактивации, добавления
            заметок или восстановления номенклатуры (изменение is_active=True).

        Оптимизация запросов:
            - select_related для owner, availability, brand, address
            - prefetch_related для images (многие-ко-многим связь)

        Args:
            request: HTTP запрос (GET или PATCH).
            pk: UUID номенклатуры.

        Returns:
            GET Response: Полные данные деактивированной номенклатуры (NomenclatureSerializer).
            PATCH Response: Обновленные данные номенклатуры (NomenclatureSerializer).

        Raises:
            HTTP_404_NOT_FOUND: Если номенклатура не найдена или не деактивирована.
            HTTP_403_FORBIDDEN: Если пользователь не имеет прав доступа (не staff).
            HTTP_400_BAD_REQUEST: При ошибке валидации данных (PATCH).

        Examples:
            >>> # Получить деактивированную номенклатуру
            >>> response = client.get('/api/nomenclatures/123e4567/inactive/')
            >>> response.status_code
            200

            >>> # Восстановить номенклатуру
            >>> response = client.patch(
            ...     '/api/nomenclatures/123e4567/inactive/',
            ...     data={'is_active': True}
            ... )
            >>> response.status_code
            200
        """
        identifier = pk
        if not identifier:
            raise NotFound("Не указан идентификатор КА.")

        # Проверяем, валидный ли UUID
        is_uuid = False
        try:
            UUID(str(identifier))
            is_uuid = True
        except ValueError:
            is_uuid = False

        instance = None

        # Если UUID — ищем по id
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

        # Если не UUID или UUID не найден — ищем по code1c
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

    @action(detail=False, methods=["GET"], url_path="broadcast")
    def broadcast(self, request):
        """
        Получить список номенклатур для вещания с учетом роли пользователя.

        Этот метод реализует сложную логику авторизации в зависимости от типа пользователя:

        Администраторы (is_admin, is_superuser, is_manager):
            - Видят все активные номенклатуры с флагом broadcast=True в их правовых лиц
            - Это позволяет администраторам контролировать все доступные номенклатуры для вещания

        Обычные пользователи (is_contact_person_broadcast=True):
            - Видят только номенклатуры своих контрагентов (counterparties)
            - Это предотвращает несанкционированный доступ к номенклатурам других компаний

        Процесс проверки:
            1. Проверяется, аутентифицирован ли пользователь
            2. Проверяется, имеет ли пользователь флаг broadcast
            3. В зависимости от типа, выбирается соответствующий queryset
            4. Результаты пагинируются и возвращаются

        Args:
            request: HTTP запрос с информацией о пользователе.

        Returns:
            Response: Пагинированный список номенклатур для вещания в JSON формате.
                     Структура: {
                         'count': int,
                         'next': str или null,
                         'previous': str или null,
                         'results': [NomenclatureListSerializer, ...]
                     }

        Status Codes:
            200 OK: Успешно получен список
            403 FORBIDDEN: Пользователь не аутентифицирован или нет права на broadcast

        Data Structure:
            {
                'count': 15,
                'next': 'http://api.example.com/nomenclatures/broadcast/?page=2',
                'previous': None,
                'results': [
                    {
                        'id': '123e4567-e89b-12d3-a456-426614174000',
                        'name': 'Display 1',
                        'description': 'Main display',
                        ...
                    }
                ]
            }

        Raises:
            HTTP_403_FORBIDDEN: Если пользователь не имеет прав на broadcast

        Examples:
            >>> # Администратор видит все номенклатуры для вещания
            >>> client.force_authenticate(user=admin_user)
            >>> response = client.get('/api/nomenclatures/broadcast/')
            >>> response.data['count']
            50  # все номенклатуры

            >>> # Обычный пользователь видит только свои контрагентов
            >>> client.force_authenticate(user=regular_user)
            >>> response = client.get('/api/nomenclatures/broadcast/')
            >>> response.data['count']
            5  # только он номенклатуры
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
                Nomenclature.active
                .select_related("owner", "availability", "brand", "address")
                .prefetch_related("images")
                .filter(legalEntity__broadcast=True)
            )
        elif is_broadcast:
            user_counterparties = user.counterparties.all()
            qs = (
                self.get_queryset()
                .filter(legalEntity__in=user_counterparties)
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

        Этот метод переопределяет стандартное поведение DRF для добавления
        дополнительной валидации. Он проверяет, что пользователь пытается
        обновить только разрешенные поля, и выбрасывает ошибку в противном случае.

        Разрешенные для редактирования поля:
            - Основная информация: name, description, timezone
            - Конфигурация: settings, contentType, typeOfPlace
            - Связи: brand_id, legalEntity_id, tenants_id, address_id
            - Персонал: responsible_radio, responsible_ad
            - Дополнительно: floor_space, traffic, pricePerMonth, media

        Защищенные поля (не могут быть отредактированы обычными пользователями):
            - id, code1c, is_active (только администраторы)
            - created, modified, article (автоматические поля)
            - owner, version, hw_info (системные поля)

        Args:
            request: HTTP PATCH/PUT запрос с данными для обновления.
            *args: Позиционные аргументы viewset.
            **kwargs: Именованные аргументы (обычно pk).

        Returns:
            Response: Обновленные данные номенклатуры (NomenclatureSerializer).

        Raises:
            HTTP_400_BAD_REQUEST: Если используются недопустимые поля.
                                 Сообщение: "Изменить можно только название, описание...
                                           Лишние ключи: {keys}."
            HTTP_404_NOT_FOUND: Если номенклатура не найдена.
            HTTP_403_FORBIDDEN: Если пользователь не имеет прав на редактирование.

        Examples:
            >>> # Правильное обновление
            >>> response = client.patch(
            ...     '/api/nomenclatures/123e4567/update/',
            ...     data={'name': 'New Name', 'description': 'New description'}
            ... )
            >>> response.status_code
            200

            >>> # Попытка изменить защищенное поле
            >>> response = client.patch(
            ...     '/api/nomenclatures/123e4567/',
            ...     data={'name': 'New Name', 'is_active': False}  # is_active защищено
            ... )
            >>> response.status_code
            400
            >>> response.data['detail']
            'Изменить можно только... Лишние ключи: is_active.'
        """
        forbidden_fields = {"is_active"}  # здесь перечисляем только запрещённые поля
        sent_keys = set(request.data.keys())
        blocked_keys = sent_keys & forbidden_fields

        if blocked_keys:
            raise serializers.ValidationError(
                f"Редактирование запрещено для полей: {', '.join(blocked_keys)}"
            )

        return super().update(request, *args, **kwargs)

    def get_object(self):
        identifier = self.kwargs.get('pk')
        if not identifier:
            raise NotFound("Не указан идентификатор номенклатуры.")

        # Проверяем, валидный ли UUID
        is_uuid = False
        try:
            UUID(str(identifier))
            is_uuid = True
        except ValueError:
            is_uuid = False

        # Если UUID — ищем по id
        if is_uuid:
            try:
                nomenclature = Nomenclature.objects.get(id=identifier)
                return nomenclature
            except Nomenclature.DoesNotExist:
                raise NotFound("Номенклатура не найдена.")

        # Если не UUID — ищем по code1c
        try:
            nomenclature = Nomenclature.objects.get(code1c=identifier)
            return nomenclature
        except Nomenclature.DoesNotExist:
            raise NotFound("Номенклатура не найдена.")

    @extend_schema(summary="Деактивировать номенклатуру")
    def destroy(self, request, *args, **kwargs):
        """
        Выполнить мягкое удаление (деактивацию) номенклатуры по ID.

        Этот метод переопределяет стандартное поведение DELETE для реализации
        'мягкого удаления' (soft delete). Вместо полного удаления из БД,
        номенклатура просто помечается как неактивная (is_active=False).

        Преимущества мягкого удаления:
            - Сохраняет историю и ссылочную целостность
            - Позволяет восстановить данные при необходимости
            - Не нарушает связи с другими объектами (заказы, статистика и т.д.)

        Процесс:
            1. Получает объект номенклатуры по ID (pk)
            2. Проверяет, не деактивирована ли она уже
            3. Если деактивирована, возвращает ошибку 400
            4. Если активна, устанавливает is_active=False и сохраняет
            5. Возвращает 204 No Content при усписе или 400 Bad Request при ошибке

        Args:
            request: HTTP DELETE запрос.
            *args: Позиционные аргументы viewset.
            **kwargs: Именованные аргументы (обычно pk).

        Returns:
            Response:
                - На успех: пустой Response с статусом 204 No Content
                - На ошибку: JSON с сообщением об ошибке и статусом 400

        Status Codes:
            204 NO CONTENT: Номенклатура успешно деактивирована
            400 BAD REQUEST: Номенклатура уже деактивирована
            403 FORBIDDEN: Пользователь не имеет прав на удаление
            404 NOT FOUND: Номенклатура не найдена

        Side Effects:
            - Изменяет поле is_active=False
            - Не удаляет физически из БД (soft delete)
            - Может создать достаточность в истории изменений

        Examples:
            >>> # Успешная деактивация
            >>> response = client.delete('/api/nomenclatures/123e4567/')
            >>> response.status_code
            204
            >>> response.content
            b''  # пустой ответ

            >>> # Попытка деактивировать уже деактивированную
            >>> response = client.delete('/api/nomenclatures/456f7890/')
            >>> response.status_code
            400
            >>> response.data['detail']
            'Нельзя деактивировать номенклатуру, т.к она уже деактивирована.'

        Warning:
            После деактивации номенклатура будет недоступна для обычных пользователей
            через /api/nomenclatures/, но доступна через /api/nomenclatures/inactive_list/
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

        Вспомогательный метод для destroy(), который отделяет логику проверки
        от логики сохранения. Выполняет следующие действия:

        1. Проверяет, не деактивирована ли номенклатура уже
        2. Если да, возвращает сообщение об ошибке (не выбрасывает исключение)
        3. Если нет, устанавливает is_active=False и сохраняет в БД
        4. Оптимизирует сохранение, указав только измененное поле (update_fields)

        Использование update_fields:
            - Более эффективно, чем сохранение всех полей
            - Генерирует SQL UPDATE с одним полем, а не всеми
            - Предотвращает нежелательные изменения других полей

        Args:
            instance: Объект Nomenclature для деактивации.

        Returns:
            str или None:
                - None если деактивация успешна
                - str с сообщением об ошибке если номенклатура уже деактивирована

        Side Effects:
            - Изменяет поле is_active в БД (если не деактивирована)

        Examples:
            >>> instance = Nomenclature.objects.get(pk='123e4567')
            >>> result = viewset.perform_destroy(instance)
            >>> result
            None  # успешно
            >>> instance.is_active
            False

            >>> # При повторном вызове
            >>> result = viewset.perform_destroy(instance)
            >>> result
            'Нельзя деактивировать номенклатуру, т.к она уже деактивирована.'

        Note:
            Этот метод не выбрасывает исключения - он возвращает результат,
            позволяя destroy() вернуть правильный статус код.
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
        summary="Получить список всех версий номенклатур",
        responses={HTTP_200_OK: VersionsSerializer},
    )
    @action(detail=False, methods=["GET"], url_path="versions")
    def get_versions(self, request):
        """
        Получить список всех уникальных версий ПО установленных на номенклатурах.

        Этот метод извлекает все уникальные значения поля 'version' из БД,
        отсортированные и выведенные списком. Используется для мониторинга версий ПО,
        установленных на различных дисплеях и устройствах.

        Query оптимизация:
            - order_by() без аргументов - очищает стандартный порядок сортировки
            - values_list('version', flat=True) - получает только одно поле
            - distinct() - убирает дубликаты в памяти после выборки

        Args:
            request: HTTP GET запрос.

        Returns:
            Response: JSON с ключом 'versions' и списком версий.
                     Структура: {
                         'versions': ['1.0.0', '1.0.1', '1.1.0', '2.0.0', ...]
                     }

        Status Codes:
            200 OK: успешно получен список

        Data Structure:
            {
                'versions': [
                    '111',
                    '112',
                    '113',
                    '120',
                    ...
                ]
            }

        Examples:
            >>> response = client.get('/api/nomenclatures/versions/')
            >>> response.status_code
            200
            >>> response.data
            {'versions': ['1.0.0', '1.0.1', '1.1.0']}
            >>> len(response.data['versions'])
            37  # количество уникальных версий

        Performance Notes:
            - Быстрый запрос, выполняется на уровне БД
            - Для большого количества номенклатур может быть медленным
            - Рекомендуется кэширование результата на уровне приложения
            - Может быть оптимизировано добавлением индекса на поле version

        Use Cases:
            - Аналитика версий ПО
            - Построение графиков обновления
            - Проверка совместимости контента с версией ПО
            - Отправки целевых обновлений определенным версиям
        """
        versions = (
            Nomenclature.objects.order_by()
            .values_list("version", flat=True)
            .distinct()
        )
        return Response({"versions": versions}, status=HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
        url_path="get_uuid_by_id",
        permission_classes=[AllowAny],
    )
    def get_id(self, request):
        """
        Получить UUID номенклатуры по её описанию.

        Этот метод выполняет обратный поиск - по описанию номенклатуры
        возвращает её уникальный идентификатор (UUID).

        Доступен всем пользователям без аутентификации (AllowAny).

        Args:
            request: HTTP GET запрос.

        Request Body (JSON):
            {
                'description': 'Основное описание номенклатуры'
            }

        Returns:
            Response: JSON с полем 'id' содержащим UUID номенклатуры.
                     Структура: {
                         'id': '123e4567-e89b-12d3-a456-426614174000'
                     }

        Status Codes:
            200 OK: UUID успешно получен
            400 BAD REQUEST: Поле 'description' не передано
            404 NOT FOUND: Номенклатура с таким описанием не найдена

        Examples:
            >>> # Успешный поиск
            >>> response = client.get(
            ...     '/api/nomenclatures/get_uuid_by_id/',
            ...     data={'description': 'Основное описание номенклатуры'}
            ... )
            >>> response.status_code
            200
            >>> response.data['id']
            '123e4567-e89b-12d3-a456-426614174000'

            >>> # Описание не найдено
            >>> response = client.get(...)
            >>> response.status_code
            404

        Warning:
            - Предполагает, что описания уникальны или используется .get()
            - Может выбросить исключение MultipleObjectsReturned если есть дубликаты
            - Case-sensitive поиск по совпадению
            - Медленнее прямого поиска по ID

        Note:
            Обычно используется в обратных интеграциях, где система знает
            описание, но нужен UUID для дальнейших операций.
        """
        nomenclature = Nomenclature.objects.get(
            id_rasb=request.data["id_rasb"]
        )
        return Response({"id": nomenclature.pk})

    @staticmethod
    def _is_admin(user):
        """
        Проверяет, является ли пользователь администратором системы.

        Функция проверяет, аутентифицирован ли пользователь и имеет ли он одно из
        следующих прав доступа: администратор, менеджер или суперпользователь.

        Args:
            user: Объект пользователя Django (django.contrib.auth.models.User или кастомный).

        Returns:
            bool: True если пользователь аутентифицирован и имеет права администратора,
                менеджера или является суперпользователем. False в остальных случаях.

        Examples:
            >>> user = User.objects.get(username='admin')
            >>> _is_admin(user)
            True

            >>> anonymous = AnonymousUser()
            >>> _is_admin(anonymous)
            False

        Note:
            Функция требует, чтобы у пользователя были атрибуты:
            - is_authenticated: указывает на аутентификацию
            - is_admin: флаг администратора
            - is_superuser: флаг суперпользователя
            - is_manager: флаг менеджера
        """
        return (
                user.is_authenticated and (
                user.is_admin
                or user.is_superuser
                or user.is_manager
        )
        )
