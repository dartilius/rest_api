# orders/views.py
# -*- coding: utf-8 -*-
"""
Вьюсеты для управления заказами (рекламными и фоновыми).

НАЗНАЧЕНИЕ:
───────────────────────────────────────────────────────────────────────────────
Предоставляет REST API для CRUD операций с заказами:
- Рекламные заказы (AdOrder) — broadcast_type 0-6
- Фоновые заказы (BgOrder) — order_type 0-3

ОСНОВНЫЕ ВОЗМОЖНОСТИ:
───────────────────────────────────────────────────────────────────────────────
1. Создание заказов (один или несколько клиентов)
2. Частичное обновление (PATCH) с ограничением полей
3. Отмена заказов (DELETE /cancel/)
4. Пагинированный список с фильтрацией
5. Детальная информация о заказе

ТИПЫ ВЕЩАНИЯ РЕКЛАМЫ (broadcast_type):
───────────────────────────────────────────────────────────────────────────────
0 - По времени работы точки
1 - Начало работы + смещение по времени
2 - Конец работы - смещение по времени
3 - Конкретные часы
4 - С открытия до фиксированного часа
5 - С фиксированного часа до закрытия
6 - Старт по событию

ТИПЫ ФОНОВЫХ ЗАКАЗОВ (order_type):
───────────────────────────────────────────────────────────────────────────────
0 - Фоновая музыка
1 - Фоновые видео
2 - Фоновые картинки
3 - Бегущая строка

СТАТУСЫ ЗАКАЗОВ (status):
───────────────────────────────────────────────────────────────────────────────
0 - Ожидает эфира
1 - В эфире
2 - Завершён
3 - Отменён
4 - Ошибка

ПРИМЕРЫ ЗАПРОСОВ:
───────────────────────────────────────────────────────────────────────────────
Создание рекламного заказа с типом 3 (конкретные часы):
    POST /api/adorders/
    {
        "playlist": "e33fa97f-4984-4a1a-9a1c-74a0f544dc8b",
        "clients": ["5778e050-454d-4e5e-ae0f-bb584979552c"],
        "name": "Test_adadadada",
        "broadcast_interval": {
            "lower": "2026-07-27 09:00:00",
            "upper": "2026-07-28 18:00:00"
        },
        "broadcast_type": 3,
        "parameters": {
            "times_in_hour": 4,
            "start_time": "12:00:00",
            "end_time": "18:00:00"
        }
    }

Создание фонового заказа (музыка):
    POST /api/bgorders/
    {
        "playlist": "3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c",
        "clients": ["d6578da7-50e0-49f4-81bd-eba08474b950"],
        "name": "Заказ фоновой музыки",
        "order_type": 0,
        "broadcast_interval": {
            "lower": "2026-05-05 09:00:00",
            "upper": "2026-05-11 18:00:00"
        },
        "parameters": {}
    }

Отмена заказа:
    DELETE /api/adorders/{id}/cancel/

Получить список заказов:
    GET /api/adorders/?status=1&created=2026-07-01,2026-07-31

Получить детали заказа:
    GET /api/adorders/{id}/

ОБНОВЛЕНИЕ ЗАКАЗОВ:
───────────────────────────────────────────────────────────────────────────────
Рекламные заказы можно обновлять только в полях:
    - name (название)
    - description (описание)
    - playlist (плейлист)
    - slides (слайды)

Фоновые заказы можно обновлять только в полях:
    - name (название)
    - description (описание)
    - playlist (плейлист)

При обновлении плейлиста или слайдов автоматически создаётся репликация.

АВТОРИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
StaffCUDAuthRetrieve — только авторизованные сотрудники имеют доступ.
"""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample
)
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST
)

from api.constants import (
    restricted_update,
    DetailSerializer,
    DEFAULT_SCHEMA_RESPONSES,
    DEFAULT_SCHEMA_EXAMPLES
)
from orders.filters import AdOrderFilter, BgOrderFilter
from orders.serializers import (
    AdOrderSerializer,
    AdOrderListSerializer,
    BgOrderSerializer,
    BgOrderListSerializer
)
from orders.models import AdOrder, BgOrder
from orders.tasks import (
    create_ad_order_task,
    update_ad_order_task,
    cancel_ad_order_task,
    create_bg_order_task,
    update_bg_order_task,
    cancel_bg_order_task
)
from users.permissions import StaffCUDAuthRetrieve


class NoDeleteViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    Базовый вьюсет без поддержки метода DELETE.

    Используется для всех вьюсетов заказов, так как удаление
    выполняется через отдельный эндпоинт /cancel/.
    """
    pass


@extend_schema_view(
    partial_update=extend_schema(
        summary='Обновить рекламный заказ',
        description=(
            'Частичное обновление рекламного заказа.\n\n'
            'Доступны для обновления только поля:\n'
            '  - name (название)\n'
            '  - description (описание)\n'
            '  - playlist (плейлист)\n'
            '  - slides (слайды)\n\n'
            'При обновлении плейлиста или слайдов автоматически '
            'создаётся репликация для отправки на клиент.'
        ),
        examples=DEFAULT_SCHEMA_EXAMPLES + [
            OpenApiExample(
                'Данные для обновления заказа со слайдами.',
                value={
                    'name': 'Иное название заказа',
                    'description': 'Иное описание заказа',
                    'playlist': '40e6215d-b5c6-4896-987c-f30f3678f608',
                    'slides': {
                        '6ecd8c99-4036-403d-bf84-cf8400f67836': [
                            '3f333df6-90a4-4fda-8dd3-9485d27cee36'
                        ]
                    }
                },
                request_only=True
            ),
            OpenApiExample(
                'Запрещенное поле для обновления',
                value={'detail': 'Нельзя обновить поля: status'},
                status_codes=[HTTP_400_BAD_REQUEST],
                response_only=True
            )
        ],
        responses={HTTP_200_OK: AdOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
    ),
    list=extend_schema(
        summary='Получить пагинированный список рекламных заказов',
        description=(
            'Возвращает список рекламных заказов с пагинацией и фильтрацией.\n\n'
            'Доступные фильтры:\n'
            '  - status — статус заказа (0-4)\n'
            '  - owner — создатель (по имени)\n'
            '  - name — частичное совпадение по названию\n'
            '  - client — частичное совпадение по клиенту\n'
            '  - brc_type — тип вещания (0-6)\n'
            '  - created — диапазон дат создания (YYYY-MM-DD,YYYY-MM-DD)\n'
            '  - since — диапазон дат начала вещания (YYYY-MM-DD,YYYY-MM-DD)\n'
            '  - until — диапазон дат окончания вещания (YYYY-MM-DD,YYYY-MM-DD)'
        ),
        responses={
            HTTP_200_OK: AdOrderListSerializer(many=True)
        } | DEFAULT_SCHEMA_RESPONSES
    ),
    retrieve=extend_schema(
        summary='Получить расшифровку рекламного заказа',
        description=(
            'Возвращает полную информацию о рекламном заказе, '
            'включая параметры, слайды и связанные объекты.'
        ),
        examples=[
            OpenApiExample(
                'Заказ с типом 0 (без слайдов)',
                description=(
                    'Заказ по режиму работы точки без слайдов, '
                    'его время в эфире зависит от настроек номенклатуры.'
                ),
                status_codes=[HTTP_200_OK],
                response_only=True,
                value={
                    'id': 'e3d9f55e-8504-498d-900c-0a48cd27fbdb',
                    'name': 'Наименование заказа с типом 0',
                    'description': 'Текстовое описание заказа, не является обязательным полем.',
                    'owner': {'full_name': 'Фамилия Имя'},
                    'playlist': {
                        'id': '57c42879-2a80-4304-9551-1c02011f559b',
                        'name': 'Наименование плейлиста',
                        'files_count': 100500
                    },
                    'slides': 'null',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 0,
                    'parameters': {
                        'times_in_hour': 4,
                        'weight': 0
                    },
                    'status': 0,
                    'created': '2025-04-28 22:36:04',
                    'client': {
                        'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
                        'name': '!!! #Test 8 Борисов И.'
                    }
                }
            ),
            OpenApiExample(
                'Заказ с типом 1 (без слайдов)',
                description=(
                    'Заказ будет в эфире от начала работы магазина '
                    'и проигрываться в течение часа. '
                    'Добавляется дополнительный параметр '
                    'timedelta - смещение по времени, '
                    'от какого времени начнет играть заказ, например 5 минут, '
                    'этот параметр не может быть менее минуты.'
                ),
                status_codes=[HTTP_200_OK],
                response_only=True,
                value={
                    'id': '88a70e05-ce8e-4b26-8d28-94f9eb59e03b',
                    'name': 'Наименование заказа с типом 1',
                    'description': 'null',
                    'owner': {'full_name': 'Фамилия Имя'},
                    'playlist': {
                        'id': '57c42879-2a80-4304-9551-1c02011f559b',
                        'name': 'Наименование плейлиста',
                        'files_count': 1337
                    },
                    'slides': 'null',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 1,
                    'parameters': {
                        'times_in_hour': 4,
                        'weight': 0,
                        'timedelta': [0, 5, 0]
                    },
                    'status': 0,
                    'created': '2025-04-28 22:36:04',
                    'client': {
                        'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
                        'name': '!!! #Test 8 Борисов И.'
                    }
                }
            ),
            OpenApiExample(
                'Заказ с типом 2 (без слайдов)',
                description=(
                    'Заказ с типом 2 будет играть от указанного смещения '
                    'по времени до окончания работы точки.'
                ),
                status_codes=[HTTP_200_OK],
                response_only=True,
                value={
                    'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
                    'name': 'Название заказа с типом 2',
                    'owner': {'full_name': 'Фамилия Имя'},
                    'description': 'null',
                    'playlist': {
                        'id': '57c42879-2a80-4304-9551-1c02011f559b',
                        'name': 'Наименование плейлиста',
                        'files_count': 1337
                    },
                    'slides': 'null',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 2,
                    'parameters': {
                        'times_in_hour': 1,
                        'weight': 0,
                        'timedelta': [0, 30, 0]
                    },
                    'status': 0,
                    'created': '2025-04-28 22:36:04',
                    'client': {
                        'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
                        'name': '!!! #Test 8 Борисов И.'
                    }
                }
            ),
            OpenApiExample(
                'Заказ с типом 3 (без слайдов)',
                description=(
                    'Заказ с типом 3 будет играть от указанного времени '
                    'start_time и до указанного времени end_time вне '
                    'зависимости от изменений режима работы точки.'
                ),
                status_codes=[HTTP_200_OK],
                response_only=True,
                value={
                    'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
                    'name': 'Название заказа с типом 3',
                    'owner': {'full_name': 'Фамилия Имя'},
                    'description': 'null',
                    'playlist': {
                        'id': '57c42879-2a80-4304-9551-1c02011f559b',
                        'name': 'Наименование плейлиста',
                        'files_count': 420
                    },
                    'slides': 'null',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 3,
                    'parameters': {
                        'times_in_hour': 1,
                        'start_time': '12:00:00',
                        'end_time': '18:00:00',
                        'weight': 30,
                        'timedelta': [0, 30, 0]
                    },
                    'status': 0,
                    'created': '2025-04-28 22:36:04',
                    'client': {
                        'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
                        'name': '!!! #Test 8 Борисов И.'
                    }
                }
            ),
            OpenApiExample(
                'Заказ с типом 4 (без слайдов)',
                description=(
                    'Заказ с типом 4 будет проигрываться с момента '
                    'открытия магазина и до указанного времени end_time.'
                ),
                status_codes=[HTTP_200_OK],
                response_only=True,
                value={
                    'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
                    'name': 'Название заказа с типом 4',
                    'owner': {'full_name': 'Фамилия Имя'},
                    'description': 'null',
                    'playlist': {
                        'id': '57c42879-2a80-4304-9551-1c02011f559b',
                        'name': 'Наименование плейлиста',
                        'files_count': 420
                    },
                    'slides': 'null',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 4,
                    'parameters': {
                        'times_in_hour': 1,
                        'end_time': '12:00:00',
                        'weight': 30,
                        'timedelta': [0, 5, 0]
                    },
                    'status': 0,
                    'created': '2025-04-28 22:36:04',
                    'client': {
                        'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
                        'name': '!!! #Test 8 Борисов И.'
                    }
                }
            ),
            OpenApiExample(
                'Заказ с типом 5 (без слайдов)',
                description=(
                    'Заказ с типом 5 будет проигрываться от '
                    'указанного времени start_time '
                    'до времени закрытия магазина.'
                ),
                status_codes=[HTTP_200_OK],
                response_only=True,
                value={
                    'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
                    'name': 'Название заказа с типом 5',
                    'owner': {'full_name': 'Фамилия Имя'},
                    'description': 'null',
                    'playlist': {
                        'id': '57c42879-2a80-4304-9551-1c02011f559b',
                        'name': 'Наименование плейлиста',
                        'files_count': 111
                    },
                    'slides': 'null',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 5,
                    'parameters': {
                        'times_in_hour': 1,
                        'start_time': '18:00:00',
                        'weight': 90,
                        'timedelta': [0, 5, 0]
                    },
                    'status': 0,
                    'created': '2025-04-28 22:36:04',
                    'client': {
                        'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
                        'name': '!!! #Test 8 Борисов И.'
                    }
                }
            ),
            OpenApiExample(
                'Заказ со слайдами (с типом 0)',
                description='Пример заказа созданного со слайдами',
                status_codes=[HTTP_200_OK],
                response_only=True,
                value={
                    'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
                    'name': 'Название заказа с типом 0',
                    'owner': {'full_name': 'Фамилия Имя'},
                    'description': 'null',
                    'playlist': {
                        'id': '57c42879-2a80-4304-9551-1c02011f559b',
                        'name': 'Наименование плейлиста',
                        'files_count': 420
                    },
                    'slides': {
                        'd3c90f33-af4f-496b-ac3d-50db3d72a8c0': [
                            'af789a1a-7489-490a-9a80-af4576adad7b',
                            'ceaf3dcc-7475-4088-ba11-a92eb35d0f1d'
                        ]
                    },
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 0,
                    'parameters': {
                        'times_in_hour': 1,
                        'weight': 50,
                    },
                    'status': 0,
                    'created': '2025-04-28 22:36:04',
                    'client': {
                        'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
                        'name': '!!! #Test 8 Борисов И.'
                    }
                }
            )
        ],
        responses={HTTP_200_OK: AdOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
    ),
    create=extend_schema(
        summary='Создать рекламный заказ',
        description=(
            'Создание одного или нескольких рекламных заказов.\n\n'
            'Для создания нескольких заказов передайте список клиентов '
            'в поле clients. Будет создан отдельный заказ для каждого клиента.\n\n'
            'Обязательные поля:\n'
            '  - playlist (ID плейлиста)\n'
            '  - clients (список ID клиентов)\n'
            '  - name (название заказа)\n'
            '  - broadcast_interval (интервал вещания)\n'
            '  - broadcast_type (тип вещания 0-6)\n'
            '  - parameters (параметры в зависимости от типа)\n\n'
            'Подробное описание параметров для каждого типа вещания:\n\n'
            'Тип 0 (по времени работы):\n'
            '  - times_in_hour (обязательно): 1, 2, 3, 4, 6, 12\n'
            '  - weight (опционально): 0-100, по умолчанию 50\n\n'
            'Тип 1 (открытие + смещение):\n'
            '  - times_in_hour (обязательно)\n'
            '  - timedelta (обязательно): "HH:MM:SS" или "MM:SS"\n'
            '  - weight (опционально)\n\n'
            'Тип 2 (закрытие - смещение):\n'
            '  - times_in_hour (обязательно)\n'
            '  - timedelta (обязательно): "HH:MM:SS" или "MM:SS"\n'
            '  - weight (опционально)\n\n'
            'Тип 3 (конкретные часы):\n'
            '  - times_in_hour (обязательно)\n'
            '  - start_time (обязательно): "HH:MM:SS"\n'
            '  - end_time (обязательно): "HH:MM:SS"\n'
            '  - weight (опционально)\n\n'
            'Тип 4 (открытие до часа):\n'
            '  - times_in_hour (обязательно)\n'
            '  - end_time (обязательно): "HH:MM:SS"\n'
            '  - weight (опционально)\n\n'
            'Тип 5 (час до закрытия):\n'
            '  - times_in_hour (обязательно)\n'
            '  - start_time (обязательно): "HH:MM:SS"\n'
            '  - weight (опционально)\n\n'
            'Тип 6 (по событию):\n'
            '  - times_in_hour (обязательно)\n'
            '  - event (обязательно): click, door_open, blablabla\n'
            '  - active_ad (обязательно): skip, stop, wait_until_end\n'
            '  - weight (опционально)'
        ),
        request=AdOrderSerializer,
        examples=[
            OpenApiExample(
                'Заказ с типом 0 (вариант 1)',
                description=(
                    'Заказ с типом 0, на одну номенклатуру, '
                    'без слайдов, 4 выхода в час без указания приоритета.\n'
                    'Приоритет (вес) заказа по умолчанию ставится 50.'
                ),
                request_only=True,
                value={
                    'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
                    'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
                    'name': 'Наименование заказа',
                    'description': 'Не обязательно заполнять',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 0,
                    'parameters': {'times_in_hour': 4}
                }
            ),
            OpenApiExample(
                'Заказ с типом 0 (вариант 2)',
                description=(
                    'Заказ с типом 0, на несколько номенклатур, '
                    'без слайдов, 4 выхода в час без указания приоритета.\n'
                    'Приоритет (вес) заказа по умолчанию ставится 50.'
                ),
                request_only=True,
                value={
                    'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
                    'clients': [
                        'd6578da7-50e0-49f4-81bd-eba08474b950',
                        '163280f9-f40d-4d08-ac57-5fa2e63f479d',
                        'e6a58506-d03a-4880-923c-011490b03f96'
                    ],
                    'name': 'Наименование заказа',
                    'description': 'Но заполнить его будет полезно на будущее',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 0,
                    'parameters': {'times_in_hour': 4}
                }
            ),
            OpenApiExample(
                'Заказ с типом 0 (вариант 3)',
                description=(
                    'Заказ с типом 0, на несколько номенклатур, '
                    'без слайдов, 4 выхода в час с высоким приоритетом.'
                ),
                request_only=True,
                value={
                    'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
                    'clients': [
                        'd6578da7-50e0-49f4-81bd-eba08474b950',
                        '163280f9-f40d-4d08-ac57-5fa2e63f479d',
                        'e6a58506-d03a-4880-923c-011490b03f96'
                    ],
                    'name': 'Наименование заказа',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 0,
                    'parameters': {'times_in_hour': 4, 'weight': 90}
                }
            ),
            OpenApiExample(
                'Заказ с типом 0 (вариант 4)',
                description=(
                    'Заказ с типом 0, на несколько номенклатур, '
                    'без слайдов, 4 выхода в час с низким приоритетом.'
                ),
                request_only=True,
                value={
                    'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
                    'clients': [
                        'd6578da7-50e0-49f4-81bd-eba08474b950',
                        '163280f9-f40d-4d08-ac57-5fa2e63f479d',
                        'e6a58506-d03a-4880-923c-011490b03f96'
                    ],
                    'name': 'Наименование заказа',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 0,
                    'parameters': {'times_in_hour': 4, 'weight': 10}
                }
            ),
            OpenApiExample(
                'Заказ с типом 0 (вариант 5)',
                description=(
                    'Заказ с типом 0, на одну номенклатуру, '
                    'со слайдами, 4 выхода в час без указания приоритета.\n'
                    'Приоритет (вес) заказа по умолчанию ставится 50.'
                ),
                request_only=True,
                value={
                    'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
                    'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
                    'name': 'Наименование заказа',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'slides': {
                        'd3c90f33-af4f-496b-ac3d-50db3d72a8c0': [
                            'af789a1a-7489-490a-9a80-af4576adad7b',
                            'ceaf3dcc-7475-4088-ba11-a92eb35d0f1d'
                        ]
                    },
                    'broadcast_type': 0,
                    'parameters': {'times_in_hour': 4}
                }
            ),
            OpenApiExample(
                'Заказ с типом 1',
                description='Заказ с типом 1 от начала работы + смещение по времени.',
                request_only=True,
                value={
                    'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
                    'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
                    'name': 'Наименование заказа',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 1,
                    'parameters': {'times_in_hour': 1, 'timedelta': '00:05:00'}
                }
            ),
            OpenApiExample(
                'Заказ с типом 2',
                description='Заказ с типом 2 от смещения по времени до окончания работы точки.',
                request_only=True,
                value={
                    'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
                    'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
                    'name': 'Наименование заказа',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 2,
                    'parameters': {'times_in_hour': 4, 'timedelta': '00:45:00'}
                }
            ),
            OpenApiExample(
                'Заказ с типом 3',
                description='Заказ с типом 3 от указанного времени и до указанного времени.',
                request_only=True,
                value={
                    'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
                    'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
                    'name': 'Наименование заказа',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 3,
                    'parameters': {
                        'times_in_hour': 4,
                        'start_time': '12:00:00',
                        'end_time': '18:00:00'
                    }
                }
            ),
            OpenApiExample(
                'Заказ с типом 4',
                description='Заказ с типом 4 от открытия точки и до указанного времени.',
                request_only=True,
                value={
                    'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
                    'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
                    'name': 'Наименование заказа',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 4,
                    'parameters': {
                        'times_in_hour': 4,
                        'end_time': '12:00:00'
                    }
                }
            ),
            OpenApiExample(
                'Заказ с типом 5',
                description='Заказ с типом 5 от указанного времени и до закрытия точки.',
                request_only=True,
                value={
                    'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
                    'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
                    'name': 'Наименование заказа',
                    'broadcast_interval': {
                        'lower': '2025-04-28 09:00:00',
                        'upper': '2025-05-01 18:00:00'
                    },
                    'broadcast_type': 5,
                    'parameters': {
                        'times_in_hour': 4,
                        'start_time': '18:00:00'
                    }
                }
            )
        ],
        responses={
            HTTP_201_CREATED: AdOrderSerializer
        } | DEFAULT_SCHEMA_RESPONSES
    )
)
@extend_schema(tags=['AD Orders'])
class AdOrderViewSet(NoDeleteViewSet):
    """
    ViewSet для управления рекламными заказами.

    Поддерживает все CRUD операции, кроме DELETE (используется cancel).

    Типы вещания (broadcast_type):
        0 - по режиму работы точки
        1 - от начала работы точки + смещение по времени delta
        2 - от смещения по времени delta до окончания работы точки
        3 - по конкретному времени
        4 - от начала работы точки до фиксированного времени
        5 - от фиксированного времени до окончания работы точки
        6 - старт вещания по событию

    Статусы (status):
        0 - Ожидает эфира
        1 - В эфире
        2 - Завершен
        3 - Отменен
        4 - Ошибка

    Параметры (parameters):
        weight - приоритет заказа, от 0 до 100
        times_in_hour - количество выходов в час (1, 2, 3, 4, 6, 12)
        timedelta - смещение по времени в формате "HH:MM:SS"
        start_time - время начала для типов 3 и 5
        end_time - время окончания для типов 3 и 4
        event - триггер для типа 6
        active_ad - поведение текущей рекламы для типа 6

    При создании заказа автоматически создаётся репликация для отправки на клиент.
    При обновлении плейлиста или слайдов также создаётся репликация.
    """

    queryset = AdOrder.objects.all().select_related(
        'owner',
        'client',
        'client__brand',
        'client__address__address__city__locality_type',
        'client__address__address__street__street_type',
        'playlist',
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdOrderFilter
    permission_classes = [StaffCUDAuthRetrieve]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def create(self, request, *args, **kwargs):
        """
        Создание одного или нескольких рекламных заказов.

        Процесс:
            1. Валидация данных через сериализатор.
            2. Сохранение заказов, владелец берётся из запроса.
            3. Сбор ID созданных заказов.
            4. Передача списка ID в Celery для создания репликаций в фоне.
            5. Формирование ответа в зависимости от количества заказов.

        Returns:
            Response:
                - При создании одного заказа: AdOrderSerializer (полный формат)
                - При создании нескольких заказов: AdOrderListSerializer (сжатый формат)
        """
        # 1. Валидация данных
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Сохранение заказов
        orders = serializer.save(owner=self.request.user)

        # 3. Сбор ID заказов
        orders_ids = []
        # Проверяем тип результата (может быть список или один объект)
        if isinstance(orders, list):
            for order in orders:
                orders_ids.append(str(order.id))
        else:
            orders_ids.append(str(orders.id))

        # 4. Запуск Celery задачи
        if orders_ids:
            create_ad_order_task.delay(orders_ids)

        # 5. Формирование ответа
        if isinstance(orders, list):
            if len(orders) > 1:
                response_serializer = AdOrderListSerializer(orders, many=True)
            else:
                response_serializer = AdOrderSerializer(orders[0])
        else:
            response_serializer = AdOrderSerializer(orders)

        return Response(response_serializer.data, status=HTTP_201_CREATED)

    def perform_create(self, serializer):
        """
        Создание заказов (используется в create, но мы переопределили create).

        Оставлен для совместимости с родительским классом, но не используется.
        Вся логика создания перенесена в метод create().
        """
        pass

    def update(self, request, *args, **kwargs):
        """
        Частичное обновление заказа (PATCH).

        Доступны для обновления только поля:
            - name (название)
            - description (описание)
            - playlist (плейлист)
            - slides (слайды)

        При обновлении плейлиста или слайдов автоматически создаётся репликация.

        Returns:
            Response: Обновлённый объект заказа.
        """
        error_message = (
            'Изменить можно только название, описание, '
            'плейлист и слайды. Лишние ключи: {keys}.'
        )
        updatable_fields = (
            'name',
            'description',
            'playlist',
            'slides'
        )
        kwargs.update(updatable_fields=updatable_fields, error_message=error_message)

        response = restricted_update(self, request, *args, **kwargs)

        # Если обновлён плейлист или слайды — создаём репликацию
        if 'playlist' in request.data or 'slides' in request.data:
            instance = self.get_object()
            update_ad_order_task.delay(order_id=str(instance.id))

        return response

    @extend_schema(
        summary='Отменить рекламный заказ',
        description=(
            'Отмена рекламного заказа.\n\n'
            'Заказ помечается статусом "Отменён" (3), '
            'и создаётся репликация отмены для отправки на клиент.\n\n'
            'Отменить можно только заказы со статусами 0 (Ожидает) или 1 (В эфире).'
        ),
        examples=[
            OpenApiExample(
                'Успешно отменен',
                value={'message': 'Запрос на отмену заказа принят.'},
                status_codes=[HTTP_200_OK]
            ),
            OpenApiExample(
                'Пользователь неавторизован',
                value={'detail': 'Учетные данные не были предоставлены.'},
                status_codes=[HTTP_401_UNAUTHORIZED]
            )
        ],
        responses={HTTP_200_OK: {'body': {}}} | DEFAULT_SCHEMA_RESPONSES
    )
    @action(detail=True, methods=['DELETE'])
    def cancel(self, request, pk):
        """
        Отмена заказа.

        Args:
            request: HTTP запрос.
            pk (str): UUID заказа.

        Returns:
            Response: Сообщение о принятии запроса на отмену.
        """
        cancel_ad_order_task.delay(str(pk))
        return Response(
            data={'message': 'Запрос на отмену заказа принят.'},
            status=HTTP_200_OK
        )

    def get_serializer(self, *args, **kwargs):
        """
        Выбор сериализатора в зависимости от действия.

        Для списка (list) используется AdOrderListSerializer (сжатый формат).
        Для остальных действий — AdOrderSerializer (полный формат).
        """
        if self.action == 'list':
            serializer_class = AdOrderListSerializer
        else:
            serializer_class = AdOrderSerializer

        # Если передан список данных — включаем many=True
        if 'data' in kwargs:
            data = kwargs['data']
            if isinstance(data, list):
                kwargs['many'] = True

        return serializer_class(*args, **kwargs)


@extend_schema_view(
    partial_update=extend_schema(
        summary='Обновить фоновый заказ',
        description=(
            'Частичное обновление фонового заказа.\n\n'
            'Доступны для обновления только поля:\n'
            '  - name (название)\n'
            '  - description (описание)\n'
            '  - playlist (плейлист)\n\n'
            'При обновлении плейлиста автоматически создаётся репликация.'
        ),
        examples=[
            OpenApiExample(
                name='Поля для обновления',
                value={
                    'name': 'Иное название заказа',
                    'description': 'Иное описание заказа',
                    'playlist': '40e6215d-b5c6-4896-987c-f30f3678f608'
                },
                request_only=True
            ),
            OpenApiExample(
                'Запрещенное поле для обновления',
                value={'detail': 'Нельзя обновить поля: status'},
                status_codes=[HTTP_400_BAD_REQUEST],
                response_only=True
            )
        ],
        responses={HTTP_200_OK: BgOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
    ),
    list=extend_schema(
        summary='Получить пагинированный список фоновых заказов',
        description=(
            'Возвращает список фоновых заказов с пагинацией и фильтрацией.\n\n'
            'Доступные фильтры:\n'
            '  - status — статус заказа (0-4)\n'
            '  - order_type — тип фона (0-3)\n'
            '  - owner — создатель (по имени)\n'
            '  - name — частичное совпадение по названию\n'
            '  - client — частичное совпадение по клиенту\n'
            '  - created — диапазон дат создания (YYYY-MM-DD,YYYY-MM-DD)\n'
            '  - since — диапазон дат начала вещания (YYYY-MM-DD,YYYY-MM-DD)\n'
            '  - until — диапазон дат окончания вещания (YYYY-MM-DD,YYYY-MM-DD)'
        ),
        responses={
            HTTP_200_OK: BgOrderListSerializer(many=True)
        } | DEFAULT_SCHEMA_RESPONSES
    ),
    retrieve=extend_schema(
        summary='Получить расшифровку фонового заказа',
        description=(
            'Возвращает полную информацию о фоновом заказе, '
            'включая параметры и тип контента.'
        ),
        examples=[
            OpenApiExample(
                'Заказ с типом 0 (фоновая музыка)',
                response_only=True,
                description='Заказ фоновой музыки который еще не находится в эфире',
                value={
                    'id': '0fc26d0e-6a12-4481-8edf-dfdbd374c3e6',
                    'name': 'Наименование заказа фоновой музыки',
                    'description': 'Описание заказа (опционально)',
                    'owner': {'full_name': 'Фамилия Имя'},
                    'order_type': 0,
                    'playlist': {
                        'id': '3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c',
                        'name': 'Плейлист фоновой музыки',
                        'files_count': 1337
                    },
                    'broadcast_interval': {
                        'lower': '2025-05-05 09:00:00',
                        'upper': '2025-05-11 18:00:00'
                    },
                    'parameters': {},
                    'status': 0,
                    'created': '2025-05-03 23:08:01',
                    'client': {
                        'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
                        'name': '!!! #Test 8 Борисов И.'
                    }
                }
            ),
            OpenApiExample(
                'Заказ с типом 1 (Фоновые видео)',
                response_only=True,
                description='Заказ фоновых видео, эфир которого уже завершился',
                value={
                    'id': '97196f20-2cd0-4416-9d29-147b03b48b5e',
                    'name': 'Наименование заказа фоновых видео',
                    'owner': {'full_name': 'Фамилия Имя'},
                    'order_type': 1,
                    'playlist': {
                        'id': 'a66f3388-6b84-4513-99e5-f47c64bd9ef4',
                        'name': 'Плейлист видео',
                        'files_count': 42
                    },
                    'broadcast_interval': {
                        'lower': '2025-03-07 08:00:00',
                        'upper': '2025-03-07 19:00:00'
                    },
                    'parameters': {},
                    'status': 2,
                    'created': '2025-03-06 23:08:01',
                    'client': {
                        'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
                        'name': '!!! #Test 8 Борисов И.'
                    }
                }
            ),
            OpenApiExample(
                'Заказ с типом 2 (Фоновые картинки)',
                response_only=True,
                description='Заказ фоновых картинок который был ранее отменен',
                value={
                    'id': '188edfd8-83f7-4dc2-917e-248ef6f56c77',
                    'name': 'Наименование заказа фоновых картинок',
                    'owner': {'full_name': 'Фамилия Имя'},
                    'order_type': 2,
                    'playlist': {
                        'id': '18936ac7-702c-4c9c-be2e-580f9b163016',
                        'name': 'Плейлист картинок',
                        'files_count': 127
                    },
                    'broadcast_interval': {
                        'lower': '2025-03-07 08:00:00',
                        'upper': '2025-03-07 19:00:00'
                    },
                    'parameters': {},
                    'status': 3,
                    'created': '2025-03-06 23:08:01',
                    'client': {
                        'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
                        'name': '!!! #Test 8 Борисов И.'
                    }
                }
            )
        ],
        responses={HTTP_200_OK: BgOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
    ),
    create=extend_schema(
        summary='Создать фоновый заказ',
        description=(
            'Создание одного или нескольких фоновых заказов.\n\n'
            'Для создания нескольких заказов передайте список клиентов '
            'в поле clients. Будет создан отдельный заказ для каждого клиента.\n\n'
            'Обязательные поля:\n'
            '  - playlist (ID плейлиста)\n'
            '  - clients (список ID клиентов)\n'
            '  - name (название заказа)\n'
            '  - order_type (тип фона 0-3)\n'
            '  - broadcast_interval (интервал вещания)\n\n'
            'Типы фоновых заказов (order_type):\n'
            '  0 - Фоновая музыка\n'
            '  1 - Фоновые видео\n'
            '  2 - Фоновые картинки\n'
            '  3 - Бегущая строка\n\n'
            'При создании заказа плейлист должен содержать файлы, '
            'соответствующие типу заказа (order_type).\n\n'
            'Для бессрочных заказов используется флаг is_permanent в модели BgOrder.'
        ),
        request=BgOrderSerializer,
        examples=[
            OpenApiExample(
                'Создать заказ фоновой музыки на 1 номенклатуру',
                request_only=True,
                description='Пример данных для создания заказа фоновой музыки на одну номенклатуру',
                value={
                    'playlist': '3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c',
                    'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
                    'name': 'Заказ фоновой музыки на 1 номенклатуру',
                    'description': 'Создано для примера',
                    'broadcast_interval': {
                        'lower': '2025-05-05 09:00:00',
                        'upper': '2025-05-11 18:00:00'
                    },
                    'parameters': {},
                    'order_type': 0
                }
            ),
            OpenApiExample(
                'Создать заказ фоновой музыки на несколько номенклатур',
                request_only=True,
                description='Пример данных для создания заказа фоновой музыки на 3 номенклатуры',
                value={
                    'playlist': '3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c',
                    'clients': [
                        'd6578da7-50e0-49f4-81bd-eba08474b950',
                        '163280f9-f40d-4d08-ac57-5fa2e63f479d',
                        'e6a58506-d03a-4880-923c-011490b03f96'
                    ],
                    'name': 'Заказ фоновой музыки на несколько номенклатур',
                    'description': 'Создано для примера',
                    'broadcast_interval': {
                        'lower': '2025-05-05 09:00:00',
                        'upper': '2025-05-11 18:00:00'
                    },
                    'parameters': {},
                    'order_type': 0
                }
            )
        ],
        responses={
            HTTP_201_CREATED: BgOrderSerializer
        } | DEFAULT_SCHEMA_RESPONSES
    )
)
@extend_schema(tags=['BG Orders'])
class BgOrderViewSet(NoDeleteViewSet):
    """
    ViewSet для управления фоновыми заказами.

    Поддерживает все CRUD операции, кроме DELETE (используется cancel).

    Типы фоновых заказов (order_type):
        0 - Фоновая музыка
        1 - Фоновые видео
        2 - Фоновые картинки
        3 - Бегущая строка

    Статусы (status):
        0 - Ожидает эфира
        1 - В эфире
        2 - Завершен
        3 - Отменен
        4 - Ошибка

    При создании заказа плейлист должен содержать файлы,
    соответствующие типу заказа (order_type).

    Для бессрочных заказов используется флаг is_permanent в модели BgOrder.
    """

    queryset = BgOrder.objects.all().select_related(
        'owner',
        'client',
        'client__brand',
        'client__address__address__city__locality_type',
        'client__address__address__street__street_type',
        'playlist',
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = BgOrderFilter
    permission_classes = [StaffCUDAuthRetrieve]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def create(self, request, *args, **kwargs):
        """
        Создание одного или нескольких фоновых заказов.

        Процесс:
            1. Валидация данных через сериализатор.
            2. Сохранение заказов, владелец берётся из запроса.
            3. Сбор ID созданных заказов.
            4. Передача списка ID в Celery для создания репликаций в фоне.

        Returns:
            Response:
                - При создании одного заказа: BgOrderSerializer (полный формат)
                - При создании нескольких заказов: BgOrderListSerializer (сжатый формат)
        """
        # 1. Валидация данных
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Сохранение заказов
        orders = serializer.save(owner=self.request.user)

        # 3. Сбор ID заказов
        orders_ids = [str(order.id) for order in orders]

        # 4. Запуск Celery задачи
        if orders_ids:
            create_bg_order_task.delay(orders_ids)

        # 5. Формирование ответа
        if len(orders) > 1:
            response_serializer = BgOrderListSerializer(orders, many=True)
        else:
            response_serializer = BgOrderSerializer(orders[0])

        return Response(response_serializer.data, status=HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Частичное обновление заказа (PATCH).

        Доступны для обновления только поля:
            - name (название)
            - description (описание)
            - playlist (плейлист)

        При обновлении плейлиста автоматически создаётся репликация.

        Returns:
            Response: Обновлённый объект заказа.
        """
        error_message = (
            'Изменить можно только название, описание и '
            'плейлист. Лишние ключи: {keys}.'
        )
        updatable_fields = (
            'name',
            'description',
            'playlist'
        )
        kwargs.update(updatable_fields=updatable_fields, error_message=error_message)

        response = restricted_update(self, request, *args, **kwargs)

        # Если обновлён плейлист — создаём репликацию
        if 'playlist' in request.data:
            instance = self.get_object()
            update_bg_order_task.delay(order_id=str(instance.id))

        return response

    @extend_schema(
        summary='Отменить фоновый заказ',
        description=(
            'Отмена фонового заказа.\n\n'
            'Заказ помечается статусом "Отменён" (3), '
            'и создаётся репликация отмены для отправки на клиент.\n\n'
            'Отменить можно только заказы со статусами 0 (Ожидает) или 1 (В эфире).'
        ),
        examples=[
            OpenApiExample(
                'Успешно отменен',
                value={'message': 'Запрос на отмену заказа принят.'},
                status_codes=[HTTP_200_OK],
                response_only=True
            ),
            OpenApiExample(
                'Пользователь неавторизован',
                value={'detail': 'Учетные данные не были предоставлены.'},
                status_codes=[HTTP_401_UNAUTHORIZED],
                response_only=True
            )
        ],
        responses={
            HTTP_200_OK: DetailSerializer,
            HTTP_401_UNAUTHORIZED: DetailSerializer,
        }
    )
    @action(detail=True, methods=['DELETE'])
    def cancel(self, request, pk):
        """
        Отмена заказа.

        Args:
            request: HTTP запрос.
            pk (str): UUID заказа.

        Returns:
            Response: Сообщение о принятии запроса на отмену.
        """
        cancel_bg_order_task.delay(str(pk))
        return Response(
            data={'message': 'Запрос на отмену заказа принят.'},
            status=HTTP_200_OK
        )

    def get_serializer(self, *args, **kwargs):
        """
        Выбор сериализатора в зависимости от действия.

        Для списка (list) используется BgOrderListSerializer (сжатый формат).
        Для остальных действий — BgOrderSerializer (полный формат).
        """
        if self.action == 'list':
            serializer_class = BgOrderListSerializer
        else:
            serializer_class = BgOrderSerializer

        # Если передан список данных — включаем many=True
        if 'data' in kwargs:
            data = kwargs['data']
            if isinstance(data, list):
                kwargs['many'] = True

        return serializer_class(*args, **kwargs)

# # orders/views.py
# # -*- coding: utf-8 -*-
# """
# Вьюсеты для управления заказами (рекламными и фоновыми).

# НАЗНАЧЕНИЕ:
# ───────────────────────────────────────────────────────────────────────────────
# Предоставляет REST API для CRUD операций с заказами:
# - Рекламные заказы (AdOrder) — broadcast_type 0-6
# - Фоновые заказы (BgOrder) — order_type 0-3

# ОСНОВНЫЕ ВОЗМОЖНОСТИ:
# ───────────────────────────────────────────────────────────────────────────────
# 1. Создание заказов (один или несколько клиентов)
# 2. Частичное обновление (PATCH) с ограничением полей
# 3. Отмена заказов (DELETE /cancel/)
# 4. Пагинированный список с фильтрацией
# 5. Детальная информация о заказе

# ТИПЫ ВЕЩАНИЯ РЕКЛАМЫ (broadcast_type):
# ───────────────────────────────────────────────────────────────────────────────
# 0 - По времени работы точки
# 1 - Начало работы + смещение по времени
# 2 - Конец работы - смещение по времени
# 3 - Конкретные часы
# 4 - С открытия до фиксированного часа
# 5 - С фиксированного часа до закрытия
# 6 - Старт по событию

# ТИПЫ ФОНОВЫХ ЗАКАЗОВ (order_type):
# ───────────────────────────────────────────────────────────────────────────────
# 0 - Фоновая музыка
# 1 - Фоновые видео
# 2 - Фоновые картинки
# 3 - Бегущая строка

# СТАТУСЫ ЗАКАЗОВ (status):
# ───────────────────────────────────────────────────────────────────────────────
# 0 - Ожидает эфира
# 1 - В эфире
# 2 - Завершён
# 3 - Отменён
# 4 - Ошибка

# ПРИМЕРЫ ЗАПРОСОВ:
# ───────────────────────────────────────────────────────────────────────────────
# Создание рекламного заказа с типом 3 (конкретные часы):
#     POST /api/adorders/
#     {
#         "playlist": "e33fa97f-4984-4a1a-9a1c-74a0f544dc8b",
#         "clients": ["5778e050-454d-4e5e-ae0f-bb584979552c"],
#         "name": "Test_adadadada",
#         "broadcast_interval": {
#             "lower": "2026-07-27 09:00:00",
#             "upper": "2026-07-28 18:00:00"
#         },
#         "broadcast_type": 3,
#         "parameters": {
#             "times_in_hour": 4,
#             "start_time": "12:00:00",
#             "end_time": "18:00:00"
#         }
#     }

# Создание фонового заказа (музыка):
#     POST /api/bgorders/
#     {
#         "playlist": "3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c",
#         "clients": ["d6578da7-50e0-49f4-81bd-eba08474b950"],
#         "name": "Заказ фоновой музыки",
#         "order_type": 0,
#         "broadcast_interval": {
#             "lower": "2026-05-05 09:00:00",
#             "upper": "2026-05-11 18:00:00"
#         },
#         "parameters": {}
#     }

# Отмена заказа:
#     DELETE /api/adorders/{id}/cancel/

# Получить список заказов:
#     GET /api/adorders/?status=1&created=2026-07-01,2026-07-31

# Получить детали заказа:
#     GET /api/adorders/{id}/

# ОБНОВЛЕНИЕ ЗАКАЗОВ:
# ───────────────────────────────────────────────────────────────────────────────
# Рекламные заказы можно обновлять только в полях:
#     - name (название)
#     - description (описание)
#     - playlist (плейлист)
#     - slides (слайды)

# Фоновые заказы можно обновлять только в полях:
#     - name (название)
#     - description (описание)
#     - playlist (плейлист)

# При обновлении плейлиста или слайдов автоматически создаётся репликация.

# АВТОРИЗАЦИЯ:
# ───────────────────────────────────────────────────────────────────────────────
# StaffCUDAuthRetrieve — только авторизованные сотрудники имеют доступ.
# """

# from django_filters.rest_framework import DjangoFilterBackend
# from drf_spectacular.utils import (
#     extend_schema,
#     extend_schema_view,
#     OpenApiExample
# )
# from rest_framework import viewsets, mixins
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.status import (
#     HTTP_200_OK,
#     HTTP_201_CREATED,
#     HTTP_401_UNAUTHORIZED,
#     HTTP_405_METHOD_NOT_ALLOWED,
#     HTTP_404_NOT_FOUND,
#     HTTP_400_BAD_REQUEST
# )

# from api.constants import (
#     restricted_update,
#     DetailSerializer,
#     DEFAULT_SCHEMA_RESPONSES,
#     DEFAULT_SCHEMA_EXAMPLES
# )
# from orders.filters import AdOrderFilter, BgOrderFilter
# from orders.serializers import (
#     AdOrderSerializer,
#     AdOrderListSerializer,
#     BgOrderSerializer,
#     BgOrderListSerializer
# )
# from orders.models import AdOrder, BgOrder
# from orders.tasks import (
#     create_ad_order_task,
#     update_ad_order_task,
#     cancel_ad_order_task,
#     create_bg_order_task,
#     update_bg_order_task,
#     cancel_bg_order_task
# )
# from users.permissions import StaffCUDAuthRetrieve


# class NoDeleteViewSet(
#     mixins.CreateModelMixin,
#     mixins.RetrieveModelMixin,
#     mixins.UpdateModelMixin,
#     mixins.ListModelMixin,
#     viewsets.GenericViewSet
# ):
#     """
#     Базовый вьюсет без поддержки метода DELETE.

#     Используется для всех вьюсетов заказов, так как удаление
#     выполняется через отдельный эндпоинт /cancel/.
#     """
#     pass


# @extend_schema_view(
#     partial_update=extend_schema(
#         summary='Обновить рекламный заказ',
#         description=(
#             'Частичное обновление рекламного заказа. '
#             'Доступны только поля: name, description, playlist, slides.'
#         ),
#         examples=DEFAULT_SCHEMA_EXAMPLES + [
#             OpenApiExample(
#                 'Данные для обновления заказа со слайдами.',
#                 value={
#                     'name': 'Иное название заказа',
#                     'description': 'Иное описание заказа',
#                     'playlist': '40e6215d-b5c6-4896-987c-f30f3678f608',
#                     'slides': {
#                         '6ecd8c99-4036-403d-bf84-cf8400f67836': [
#                             '3f333df6-90a4-4fda-8dd3-9485d27cee36'
#                         ]
#                     }
#                 },
#                 request_only=True
#             ),
#             OpenApiExample(
#                 'Запрещенное поле для обновления',
#                 value={'detail': 'Нельзя обновить поля: status'},
#                 status_codes=[HTTP_400_BAD_REQUEST],
#                 response_only=True
#             )
#         ],
#         responses={HTTP_200_OK: AdOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
#     ),
#     list=extend_schema(
#         summary='Получить пагинированный список рекламных заказов',
#         description=(
#             'Возвращает список рекламных заказов с пагинацией и фильтрацией.\n\n'
#             'Доступные фильтры:\n'
#             '  - status — статус заказа (0-4)\n'
#             '  - owner — создатель (по имени)\n'
#             '  - name — частичное совпадение по названию\n'
#             '  - client — частичное совпадение по клиенту\n'
#             '  - created — диапазон дат создания (YYYY-MM-DD,YYYY-MM-DD)\n'
#             '  - since — диапазон дат начала вещания (YYYY-MM-DD,YYYY-MM-DD)\n'
#             '  - until — диапазон дат окончания вещания (YYYY-MM-DD,YYYY-MM-DD)'
#         ),
#         responses={
#             HTTP_200_OK: AdOrderListSerializer(many=True)
#         } | DEFAULT_SCHEMA_RESPONSES
#     ),
#     retrieve=extend_schema(
#         summary='Получить расшифровку рекламного заказа',
#         description=(
#             'Возвращает полную информацию о рекламном заказе, '
#             'включая параметры и слайды.'
#         ),
#         examples=[
#             OpenApiExample(
#                 'Заказ с типом 0 (без слайдов)',
#                 description=(
#                     'Заказ по режиму работы точки без слайдов, '
#                     'его время в эфире зависит от настроек номенклатуры.'
#                 ),
#                 status_codes=[HTTP_200_OK],
#                 response_only=True,
#                 value={
#                     'id': 'e3d9f55e-8504-498d-900c-0a48cd27fbdb',
#                     'name': 'Наименование заказа с типом 0',
#                     'description': (
#                         'Текстовое описание заказа, '
#                         'не является обязательным полем.'
#                     ),
#                     'owner': {'full_name': 'Фамилия Имя'},
#                     'playlist': {
#                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
#                         'name': 'Наименование плейлиста',
#                         'files_count': 100500
#                     },
#                     'slides': 'null',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 0,
#                     'parameters': {
#                         'times_in_hour': 4,
#                         'weight': 0
#                     },
#                     'status': 0,
#                     'created': '2025-04-28 22:36:04',
#                     'client': {
#                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         'name': '!!! #Test 8 Борисов И.'
#                     }
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 1 (без слайдов)',
#                 description=(
#                     'Заказ будет в эфире от начала работы магазина '
#                     'и проигрываться в течении часа. '
#                     'Добавляется дополнительный параметр '
#                     'timedelta - смещение по времени, '
#                     'от какого времени начнет играть заказ, например 5 минут, '
#                     'этот параметр не может быть менее минуты.'
#                 ),
#                 status_codes=[HTTP_200_OK],
#                 response_only=True,
#                 value={
#                     'id': '88a70e05-ce8e-4b26-8d28-94f9eb59e03b',
#                     'name': 'Наименование заказа с типом 1',
#                     'description': 'null',
#                     'owner': {'full_name': 'Фамилия Имя'},
#                     'playlist': {
#                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
#                         'name': 'Наименование плейлиста',
#                         'files_count': 1337
#                     },
#                     'slides': 'null',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 1,
#                     'parameters': {
#                         'times_in_hour': 4,
#                         'weight': 0,
#                         'timedelta': [0, 5, 0]
#                     },
#                     'status': 0,
#                     'created': '2025-04-28 22:36:04',
#                     'client': {
#                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         'name': '!!! #Test 8 Борисов И.'
#                     }
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 2 (без слайдов)',
#                 description=(
#                     'Заказ с типом 2 будет играть от указанного смещения '
#                     'по времени до окончания работы точки.'
#                 ),
#                 status_codes=[HTTP_200_OK],
#                 response_only=True,
#                 value={
#                     'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
#                     'name': 'Название заказа с типом 2',
#                     'owner': {'full_name': 'Фамилия Имя'},
#                     'description': 'null',
#                     'playlist': {
#                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
#                         'name': 'Наименование плейлиста',
#                         'files_count': 1337
#                     },
#                     'slides': 'null',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 2,
#                     'parameters': {
#                         'times_in_hour': 1,
#                         'weight': 0,
#                         'timedelta': [0, 30, 0]
#                     },
#                     'status': 0,
#                     'created': '2025-04-28 22:36:04',
#                     'client': {
#                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         'name': '!!! #Test 8 Борисов И.'
#                     }
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 3 (без слайдов)',
#                 description=(
#                     'Заказ с типом 3 будет играть от указанного времени '
#                     'start_time и до указанного времени end_time вне '
#                     'зависимости от изменений режима работы точки, '
#                     'но нужно учитывать настройки громкости, '
#                     'если разместить заказ до начала работы '
#                     'и не включить звук, то заказ будет без звука.'
#                 ),
#                 status_codes=[HTTP_200_OK],
#                 response_only=True,
#                 value={
#                     'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
#                     'name': 'Название заказа с типом 3',
#                     'owner': {'full_name': 'Фамилия Имя'},
#                     'description': 'null',
#                     'playlist': {
#                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
#                         'name': 'Наименование плейлиста',
#                         'files_count': 420
#                     },
#                     'slides': 'null',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 3,
#                     'parameters': {
#                         'times_in_hour': 1,
#                         'start_time': '12:00:00',
#                         'end_time': '18:00:00',
#                         'weight': 30,
#                         'timedelta': [0, 30, 0]
#                     },
#                     'status': 0,
#                     'created': '2025-04-28 22:36:04',
#                     'client': {
#                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         'name': '!!! #Test 8 Борисов И.'
#                     }
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 4 (без слайдов)',
#                 description=(
#                     'Заказ с типом 4 будет проигрываться с момента '
#                     'открытия магазина и до указанного времени end_time.'
#                 ),
#                 status_codes=[HTTP_200_OK],
#                 response_only=True,
#                 value={
#                     'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
#                     'name': 'Название заказа с типом 4',
#                     'owner': {'full_name': 'Фамилия Имя'},
#                     'description': 'null',
#                     'playlist': {
#                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
#                         'name': 'Наименование плейлиста',
#                         'files_count': 420
#                     },
#                     'slides': 'null',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 4,
#                     'parameters': {
#                         'times_in_hour': 1,
#                         'end_time': '12:00:00',
#                         'weight': 30,
#                         'timedelta': [0, 5, 0]
#                     },
#                     'status': 0,
#                     'created': '2025-04-28 22:36:04',
#                     'client': {
#                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         'name': '!!! #Test 8 Борисов И.'
#                     }
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 5 (без слайдов)',
#                 description=(
#                     'Заказ с типом 5 будет проигрываться от '
#                     'указанного времени start_time '
#                     'до времени закрытия магазина.'
#                 ),
#                 status_codes=[HTTP_200_OK],
#                 response_only=True,
#                 value={
#                     'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
#                     'name': 'Название заказа с типом 4',
#                     'owner': {'full_name': 'Фамилия Имя'},
#                     'description': 'null',
#                     'playlist': {
#                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
#                         'name': 'Наименование плейлиста',
#                         'files_count': 111
#                     },
#                     'slides': 'null',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 5,
#                     'parameters': {
#                         'times_in_hour': 1,
#                         'start_time': '18:00:00',
#                         'weight': 90,
#                         'timedelta': [0, 5, 0]
#                     },
#                     'status': 0,
#                     'created': '2025-04-28 22:36:04',
#                     'client': {
#                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         'name': '!!! #Test 8 Борисов И.'
#                     }
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ со слайдами (с типом 0)',
#                 description=(
#                     'Пример заказа созданного со слайдами'
#                 ),
#                 status_codes=[HTTP_200_OK],
#                 response_only=True,
#                 value={
#                     'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
#                     'name': 'Название заказа с типом 0',
#                     'owner': {'full_name': 'Фамилия Имя'},
#                     'description': 'null',
#                     'playlist': {
#                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
#                         'name': 'Наименование плейлиста',
#                         'files_count': 420
#                     },
#                     'slides': {
#                         'd3c90f33-af4f-496b-ac3d-50db3d72a8c0': [
#                             'af789a1a-7489-490a-9a80-af4576adad7b',
#                             'ceaf3dcc-7475-4088-ba11-a92eb35d0f1d'
#                         ]
#                     },
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 0,
#                     'parameters': {
#                         'times_in_hour': 1,
#                         'weight': 50,
#                     },
#                     'status': 0,
#                     'created': '2025-04-28 22:36:04',
#                     'client': {
#                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         'name': '!!! #Test 8 Борисов И.'
#                     }
#                 }
#             )
#         ],
#         responses={HTTP_200_OK: AdOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
#     ),
#     create=extend_schema(
#         summary='Создать рекламный заказ',
#         description=(
#             'Создание одного или нескольких рекламных заказов.\n\n'
#             'Для создания нескольких заказов передайте список клиентов '
#             'в поле clients. Будет создан отдельный заказ для каждого клиента.\n\n'
#             'Обязательные поля: playlist, clients, name, broadcast_interval, '
#             'broadcast_type, parameters.\n\n'
#             'Для типа 0 (по времени работы) параметры:\n'
#             '  - times_in_hour (обязательно): 1, 2, 3, 4, 6, 12\n'
#             '  - weight (опционально): 0-100, по умолчанию 50\n\n'
#             'Для типа 1 (открытие + смещение):\n'
#             '  - times_in_hour (обязательно)\n'
#             '  - timedelta (обязательно): "HH:MM:SS" или "MM:SS"\n'
#             '  - weight (опционально)\n\n'
#             'Для типа 2 (закрытие - смещение):\n'
#             '  - times_in_hour (обязательно)\n'
#             '  - timedelta (обязательно): "HH:MM:SS" или "MM:SS"\n'
#             '  - weight (опционально)\n\n'
#             'Для типа 3 (конкретные часы):\n'
#             '  - times_in_hour (обязательно)\n'
#             '  - start_time (обязательно): "HH:MM:SS"\n'
#             '  - end_time (обязательно): "HH:MM:SS"\n'
#             '  - weight (опционально)\n\n'
#             'Для типа 4 (открытие до часа):\n'
#             '  - times_in_hour (обязательно)\n'
#             '  - end_time (обязательно): "HH:MM:SS"\n'
#             '  - weight (опционально)\n\n'
#             'Для типа 5 (час до закрытия):\n'
#             '  - times_in_hour (обязательно)\n'
#             '  - start_time (обязательно): "HH:MM:SS"\n'
#             '  - weight (опционально)\n\n'
#             'Для типа 6 (по событию):\n'
#             '  - times_in_hour (обязательно)\n'
#             '  - event (обязательно): click, door_open, blablabla\n'
#             '  - active_ad (обязательно): skip, stop, wait_until_end\n'
#             '  - weight (опционально)'
#         ),
#         request=AdOrderSerializer,
#         examples=[
#             OpenApiExample(
#                 'Заказ с типом 0 (вариант 1)',
#                 description=(
#                     'Заказ с типом 0, на одну номенклатуру, '
#                     'без слайдов, 4 выхода в час без указания приоритета.'
#                     'Приоритет (вес) заказа по умолчанию ставится 50.'
#                 ),
#                 request_only=True,
#                 value={
#                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
#                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
#                     'name': 'Наименование заказа',
#                     'description': 'Не обязательно заполнять',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 0,
#                     'parameters': {'times_in_hour': 4}
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 0 (вариант 2)',
#                 request_only=True,
#                 description=(
#                     'Заказ с типом 0, на несколько номенклатур, '
#                     'без слайдов, 4 выхода в час без указания приоритета.'
#                     'Приоритет (вес) заказа по умолчанию ставится 50.'
#                 ),
#                 value={
#                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
#                     'clients': [
#                         'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         '163280f9-f40d-4d08-ac57-5fa2e63f479d',
#                         'e6a58506-d03a-4880-923c-011490b03f96'
#                     ],
#                     'name': 'Наименование заказа',
#                     'description': 'Но заполнить его будет полезно на будущее',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 0,
#                     'parameters': {'times_in_hour': 4}
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 0 (вариант 3)',
#                 request_only=True,
#                 description=(
#                     'Заказ с типом 0, на несколько номенклатур, '
#                     'без слайдов, 4 выхода в час с высоким приоритетом.'
#                 ),
#                 value={
#                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
#                     'clients': [
#                         'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         '163280f9-f40d-4d08-ac57-5fa2e63f479d',
#                         'e6a58506-d03a-4880-923c-011490b03f96'
#                     ],
#                     'name': 'Наименование заказа',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 0,
#                     'parameters': {'times_in_hour': 4, 'weight': 90}
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 0 (вариант 4)',
#                 request_only=True,
#                 description=(
#                     'Заказ с типом 0, на несколько номенклатур, '
#                     'без слайдов, 4 выхода в час с низким приоритетом.'
#                 ),
#                 value={
#                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
#                     'clients': [
#                         'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         '163280f9-f40d-4d08-ac57-5fa2e63f479d',
#                         'e6a58506-d03a-4880-923c-011490b03f96'
#                     ],
#                     'name': 'Наименование заказа',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 0,
#                     'parameters': {'times_in_hour': 4, 'weight': 10}
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 0 (вариант 5)',
#                 description=(
#                     'Заказ с типом 0, на одну номенклатуру, '
#                     'со слайдами, 4 выхода в час без указания приоритета.'
#                     'Приоритет (вес) заказа по умолчанию ставится 50.'
#                 ),
#                 request_only=True,
#                 value={
#                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
#                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
#                     'name': 'Наименование заказа',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'slides': {
#                         'd3c90f33-af4f-496b-ac3d-50db3d72a8c0': [
#                             'af789a1a-7489-490a-9a80-af4576adad7b',
#                             'ceaf3dcc-7475-4088-ba11-a92eb35d0f1d'
#                         ]
#                     },
#                     'broadcast_type': 0,
#                     'parameters': {'times_in_hour': 4}
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 1',
#                 description=(
#                     'Заказ с типом 1 от начала работы + смещение по времени.'
#                 ),
#                 request_only=True,
#                 value={
#                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
#                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
#                     'name': 'Наименование заказа',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 1,
#                     'parameters': {'times_in_hour': 1, 'timedelta': '00:05:00'}
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 2',
#                 description=(
#                     'Заказ с типом 2 от смещения по времени '
#                     'до окончания работы точки.'
#                 ),
#                 request_only=True,
#                 value={
#                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
#                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
#                     'name': 'Наименование заказа',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 2,
#                     'parameters': {'times_in_hour': 4, 'timedelta': '00:45:00'}
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 3',
#                 description=(
#                     'Заказ с типом 3 от указанного времени '
#                     'и до указанного времени.'
#                 ),
#                 request_only=True,
#                 value={
#                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
#                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
#                     'name': 'Наименование заказа',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 3,
#                     'parameters': {
#                         'times_in_hour': 4,
#                         'start_time': '12:00:00',
#                         'end_time': '18:00:00'
#                     }
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 4',
#                 description=(
#                     'Заказ с типом 4 от открытия точки '
#                     'и до указанного времени.'
#                 ),
#                 request_only=True,
#                 value={
#                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
#                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
#                     'name': 'Наименование заказа',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 4,
#                     'parameters': {
#                         'times_in_hour': 4,
#                         'end_time': '12:00:00'
#                     }
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 5',
#                 description=(
#                     'Заказ с типом 4 от указанного времени '
#                     'и до закрытия точки.'
#                 ),
#                 request_only=True,
#                 value={
#                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
#                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
#                     'name': 'Наименование заказа',
#                     'broadcast_interval': {
#                         'lower': '2025-04-28 09:00:00',
#                         'upper': '2025-05-01 18:00:00'
#                     },
#                     'broadcast_type': 5,
#                     'parameters': {
#                         'times_in_hour': 4,
#                         'start_time': '18:00:00'
#                     }
#                 }
#             )
#         ],
#         responses={
#             HTTP_201_CREATED: AdOrderSerializer
#         } | DEFAULT_SCHEMA_RESPONSES
#     )
# )
# @extend_schema(tags=['AD Orders'])
# class AdOrderViewSet(NoDeleteViewSet):
#     """
#     ViewSet для управления рекламными заказами.

#     Поддерживает все CRUD операции, кроме DELETE (используется cancel).

#     Типы вещания (broadcast_type):
#         0 - по режиму работы точки
#         1 - от начала работы точки + смещение по времени delta
#         2 - от смещения по времени delta до окончания работы точки
#         3 - по конкретному времени
#         4 - от начала работы точки до фиксированного времени
#         5 - от фиксированного времени до окончания работы точки
#         6 - старт вещания по событию

#     Статусы (status):
#         0 - Ожидает эфира
#         1 - В эфире
#         2 - Завершен
#         3 - Отменен
#         4 - Ошибка

#     Параметры (parameters):
#         weight - приоритет заказа, от 0 до 100
#         times_in_hour - количество выходов в час (1, 2, 3, 4, 6, 12)
#         timedelta - смещение по времени в формате "HH:MM:SS"
#         start_time - время начала для типов 3 и 5
#         end_time - время окончания для типов 3 и 4
#         event - триггер для типа 6
#         active_ad - поведение текущей рекламы для типа 6
#     """

#     queryset = AdOrder.objects.all().select_related(
#         'owner', 'client', 'playlist'
#     )
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = AdOrderFilter
#     permission_classes = [StaffCUDAuthRetrieve]
#     http_method_names = ['get', 'post', 'patch', 'delete']

#     def perform_create(self, serializer):
#         """
#         Создание заказов.

#         Процесс:
#             0. Валидация данных через сериализатор.
#             1. Сохранение заказов, владелец берётся из запроса.
#             2. Сбор ID созданных заказов.
#             3. Передача списка ID в Celery для создания репликаций в фоне.

#         Args:
#             serializer: Валидированный сериализатор с данными заказа.
#         """
#         # 0. Валидация данных
#         serializer.is_valid(raise_exception=True)

#         # 1. Сохранение заказов с указанием владельца
#         orders_list = serializer.save(owner=self.request.user)

#         # 2. Сбор ID заказов
#         orders_ids = []

#         # 🔥 Проверяем тип результата (может быть список или один объект)
#         if isinstance(orders_list, list):
#             # Несколько заказов (несколько клиентов)
#             for order in orders_list:
#                 orders_ids.append(str(order.id))
#         else:
#             # Один заказ (один клиент)
#             orders_ids.append(str(orders_list.id))

#         # 3. Запуск Celery задачи для создания репликаций
#         if orders_ids:
#             create_ad_order_task.delay(orders_ids)

#     def update(self, request, *args, **kwargs):
#         """
#         Частичное обновление заказа (PATCH).

#         Доступны для обновления только поля:
#             - name (название)
#             - description (описание)
#             - playlist (плейлист)
#             - slides (слайды)

#         При обновлении плейлиста или слайдов автоматически создаётся репликация.

#         Returns:
#             Response: Обновлённый объект заказа.
#         """
#         error_message = (
#             'Изменить можно только название, описание, '
#             'плейлист и слайды. Лишние ключи: {keys}.'
#         )
#         updatable_fields = (
#             'name',
#             'description',
#             'playlist',
#             'slides'
#         )
#         kwargs.update(updatable_fields=updatable_fields, error_message=error_message)

#         response = restricted_update(self, request, *args, **kwargs)

#         # Если обновлён плейлист или слайды — создаём репликацию
#         if 'playlist' in request.data or 'slides' in request.data:
#             instance = self.get_object()
#             update_ad_order_task.delay(order_id=str(instance.id))

#         return response

#     @extend_schema(
#         summary='Отменить рекламный заказ',
#         description=(
#             'Отмена рекламного заказа.\n\n'
#             'Заказ помечается статусом "Отменён" (3), '
#             'и создаётся репликация отмены для отправки на клиент.\n\n'
#             'Отменить можно только заказы со статусами 0 (Ожидает) или 1 (В эфире).'
#         ),
#         examples=[
#             OpenApiExample(
#                 'Успешно отменен',
#                 value={'message': 'Запрос на отмену заказа принят.'},
#                 status_codes=[HTTP_200_OK]
#             ),
#             OpenApiExample(
#                 'Пользователь неавторизован',
#                 value={'detail': 'Учетные данные не были предоставлены.'},
#                 status_codes=[HTTP_401_UNAUTHORIZED]
#             )
#         ],
#         responses={HTTP_200_OK: {'body': {}}} | DEFAULT_SCHEMA_RESPONSES
#     )
#     @action(detail=True, methods=['DELETE'])
#     def cancel(self, request, pk):
#         """
#         Отмена заказа.

#         Args:
#             request: HTTP запрос.
#             pk (str): UUID заказа.

#         Returns:
#             Response: Сообщение о принятии запроса на отмену.
#         """
#         cancel_ad_order_task.delay(str(pk))
#         return Response(
#             data={'message': 'Запрос на отмену заказа принят.'},
#             status=HTTP_200_OK
#         )

#     def get_serializer(self, *args, **kwargs):
#         """
#         Выбор сериализатора в зависимости от действия.

#         Для списка (list) используется AdOrderListSerializer (сжатый формат).
#         Для остальных действий — AdOrderSerializer (полный формат).
#         """
#         if self.action == 'list':
#             serializer_class = AdOrderListSerializer
#         else:
#             serializer_class = AdOrderSerializer

#         # Если передан список данных — включаем many=True
#         if 'data' in kwargs:
#             data = kwargs['data']
#             if isinstance(data, list):
#                 kwargs['many'] = True

#         return serializer_class(*args, **kwargs)


# @extend_schema_view(
#     partial_update=extend_schema(
#         summary='Обновить фоновый заказ',
#         description=(
#             'Частичное обновление фонового заказа. '
#             'Доступны только поля: name, description, playlist.'
#         ),
#         examples=[
#             OpenApiExample(
#                 name='Поля для обновления',
#                 value={
#                     'name': 'Иное название заказа',
#                     'description': 'Иное описание заказа',
#                     'playlist': '40e6215d-b5c6-4896-987c-f30f3678f608'
#                 },
#                 request_only=True
#             ),
#             OpenApiExample(
#                 'Запрещенное поле для обновления',
#                 value={'detail': 'Нельзя обновить поля: status'},
#                 status_codes=[HTTP_400_BAD_REQUEST],
#                 response_only=True
#             )
#         ],
#         responses={HTTP_200_OK: BgOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
#     ),
#     list=extend_schema(
#         summary='Получить пагинированный список фоновых заказов',
#         description=(
#             'Возвращает список фоновых заказов с пагинацией и фильтрацией.\n\n'
#             'Доступные фильтры:\n'
#             '  - status — статус заказа (0-4)\n'
#             '  - order_type — тип фона (0-3)\n'
#             '  - owner — создатель (по имени)\n'
#             '  - name — частичное совпадение по названию\n'
#             '  - client — частичное совпадение по клиенту\n'
#             '  - created — диапазон дат создания (YYYY-MM-DD,YYYY-MM-DD)\n'
#             '  - since — диапазон дат начала вещания\n'
#             '  - until — диапазон дат окончания вещания'
#         ),
#         responses={
#             HTTP_200_OK: BgOrderListSerializer(many=True)
#         } | DEFAULT_SCHEMA_RESPONSES
#     ),
#     retrieve=extend_schema(
#         summary='Получить расшифровку фонового заказа',
#         description=(
#             'Возвращает полную информацию о фоновом заказе, '
#             'включая параметры и тип контента.'
#         ),
#         examples=[
#             OpenApiExample(
#                 'Заказ с типом 0 (фоновая музыка)',
#                 response_only=True,
#                 description='Заказ фоновой музыки который еще не находится в эфире',
#                 value={
#                     'id': '0fc26d0e-6a12-4481-8edf-dfdbd374c3e6',
#                     'name': 'Наименование заказа фоновой музыки',
#                     'description': 'Описание заказа (опционально)',
#                     'owner': {'full_name': 'Фамилия Имя'},
#                     'order_type': 0,
#                     'playlist': {
#                         'id': '3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c',
#                         'name': 'Плейлист фоновой музыки',
#                         'files_count': 1337
#                     },
#                     'broadcast_interval': {
#                         'lower': '2025-05-05 09:00:00',
#                         'upper': '2025-05-11 18:00:00'
#                     },
#                     'parameters': {},
#                     'status': 0,
#                     'created': '2025-05-03 23:08:01',
#                     'client': {
#                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         'name': '!!! #Test 8 Борисов И.'
#                     }
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 1 (Фоновые видео)',
#                 response_only=True,
#                 description='Заказ фоновых видео, эфир которого уже завершился',
#                 value={
#                     'id': '97196f20-2cd0-4416-9d29-147b03b48b5e',
#                     'name': 'Наименование заказа фоновых видео',
#                     'owner': {'full_name': 'Фамилия Имя'},
#                     'order_type': 1,
#                     'playlist': {
#                         'id': 'a66f3388-6b84-4513-99e5-f47c64bd9ef4',
#                         'name': 'Плейлист видео',
#                         'files_count': 42
#                     },
#                     'broadcast_interval': {
#                         'lower': '2025-03-07 08:00:00',
#                         'upper': '2025-03-07 19:00:00'
#                     },
#                     'parameters': {},
#                     'status': 2,
#                     'created': '2025-03-06 23:08:01',
#                     'client': {
#                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         'name': '!!! #Test 8 Борисов И.'
#                     }
#                 }
#             ),
#             OpenApiExample(
#                 'Заказ с типом 2 (Фоновые картинки)',
#                 response_only=True,
#                 description='Заказ фоновых картинок который был ранее отменен',
#                 value={
#                     'id': '188edfd8-83f7-4dc2-917e-248ef6f56c77',
#                     'name': 'Наименование заказа фоновых картинок',
#                     'owner': {'full_name': 'Фамилия Имя'},
#                     'order_type': 2,
#                     'playlist': {
#                         'id': '18936ac7-702c-4c9c-be2e-580f9b163016',
#                         'name': 'Плейлист картинок',
#                         'files_count': 127
#                     },
#                     'broadcast_interval': {
#                         'lower': '2025-03-07 08:00:00',
#                         'upper': '2025-03-07 19:00:00'
#                     },
#                     'parameters': {},
#                     'status': 3,
#                     'created': '2025-03-06 23:08:01',
#                     'client': {
#                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         'name': '!!! #Test 8 Борисов И.'
#                     }
#                 }
#             )
#         ],
#         responses={HTTP_200_OK: BgOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
#     ),
#     create=extend_schema(
#         summary='Создать фоновый заказ',
#         description=(
#             'Создание одного или нескольких фоновых заказов.\n\n'
#             'Для создания нескольких заказов передайте список клиентов '
#             'в поле clients. Будет создан отдельный заказ для каждого клиента.\n\n'
#             'Обязательные поля: playlist, clients, name, order_type, '
#             'broadcast_interval.\n\n'
#             'Типы фоновых заказов (order_type):\n'
#             '  0 - Фоновая музыка\n'
#             '  1 - Фоновые видео\n'
#             '  2 - Фоновые картинки\n'
#             '  3 - Бегущая строка\n\n'
#             'Параметры (parameters):\n'
#             '  - weight (опционально): 0-100, по умолчанию 50\n'
#             '  - times_in_hour (опционально): 1, 2, 3, 4, 6, 12'
#         ),
#         request=BgOrderSerializer,
#         examples=[
#             OpenApiExample(
#                 'Создать заказ фоновой музыки на 1 номенклатуру',
#                 request_only=True,
#                 description='Пример данных для создания заказа фоновой музыки на одну номенклатуру',
#                 value={
#                     'playlist': '3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c',
#                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
#                     'name': 'Заказ фоновой музыки на 1 номенклатуру',
#                     'description': 'Создано для примера',
#                     'broadcast_interval': {
#                         'lower': '2025-05-05 09:00:00',
#                         'upper': '2025-05-11 18:00:00'
#                     },
#                     'parameters': {},
#                     'order_type': 0
#                 }
#             ),
#             OpenApiExample(
#                 'Создать заказ фоновой музыки на несколько номенклатур',
#                 request_only=True,
#                 description='Пример данных для создания заказа фоновой музыки на 3 номенклатуры',
#                 value={
#                     'playlist': '3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c',
#                     'clients': [
#                         'd6578da7-50e0-49f4-81bd-eba08474b950',
#                         '163280f9-f40d-4d08-ac57-5fa2e63f479d',
#                         'e6a58506-d03a-4880-923c-011490b03f96'
#                     ],
#                     'name': 'Заказ фоновой музыки на несколько номенклатур',
#                     'description': 'Создано для примера',
#                     'broadcast_interval': {
#                         'lower': '2025-05-05 09:00:00',
#                         'upper': '2025-05-11 18:00:00'
#                     },
#                     'parameters': {},
#                     'order_type': 0
#                 }
#             )
#         ],
#         responses={
#             HTTP_201_CREATED: BgOrderSerializer
#         } | DEFAULT_SCHEMA_RESPONSES
#     )
# )
# @extend_schema(tags=['BG Orders'])
# class BgOrderViewSet(NoDeleteViewSet):
#     """
#     ViewSet для управления фоновыми заказами.

#     Поддерживает все CRUD операции, кроме DELETE (используется cancel).

#     Типы фоновых заказов (order_type):
#         0 - Фоновая музыка
#         1 - Фоновые видео
#         2 - Фоновые картинки
#         3 - Бегущая строка

#     Статусы (status):
#         0 - Ожидает эфира
#         1 - В эфире
#         2 - Завершен
#         3 - Отменен
#         4 - Ошибка

#     При создании заказа плейлист должен содержать файлы,
#     соответствующие типу заказа (order_type).

#     Для бессрочных заказов используется флаг is_permanent в модели BgOrder.
#     """

#     queryset = BgOrder.objects.all().select_related(
#         'owner', 'client', 'playlist'
#     )
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = BgOrderFilter
#     permission_classes = [StaffCUDAuthRetrieve]
#     http_method_names = ['get', 'post', 'patch', 'delete']

#     def create(self, request, *args, **kwargs):
#         """
#         Создание одного или нескольких фоновых заказов.

#         Процесс:
#             1. Валидация данных через сериализатор.
#             2. Сохранение заказов, владелец берётся из запроса.
#             3. Сбор ID созданных заказов.
#             4. Передача списка ID в Celery для создания репликаций в фоне.

#         Returns:
#             Response:
#                 - При создании одного заказа: BgOrderSerializer (полный формат)
#                 - При создании нескольких заказов: BgOrderListSerializer (сжатый формат)
#         """
#         # 1. Валидация данных
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         # 2. Сохранение заказов
#         orders = serializer.save(owner=self.request.user)

#         # 3. Сбор ID заказов
#         orders_ids = [str(order.id) for order in orders]

#         # 4. Запуск Celery задачи
#         if orders_ids:
#             create_bg_order_task.delay(orders_ids)

#         # Выбор сериализатора для ответа
#         if len(orders) > 1:
#             response_serializer = BgOrderListSerializer(orders, many=True)
#         else:
#             response_serializer = BgOrderSerializer(orders[0])

#         return Response(response_serializer.data, status=HTTP_201_CREATED)

#     def update(self, request, *args, **kwargs):
#         """
#         Частичное обновление заказа (PATCH).

#         Доступны для обновления только поля:
#             - name (название)
#             - description (описание)
#             - playlist (плейлист)

#         При обновлении плейлиста автоматически создаётся репликация.

#         Returns:
#             Response: Обновлённый объект заказа.
#         """
#         error_message = (
#             'Изменить можно только название, описание и '
#             'плейлист. Лишние ключи: {keys}.'
#         )
#         updatable_fields = (
#             'name',
#             'description',
#             'playlist'
#         )
#         kwargs.update(updatable_fields=updatable_fields, error_message=error_message)

#         response = restricted_update(self, request, *args, **kwargs)

#         # Если обновлён плейлист — создаём репликацию
#         if 'playlist' in request.data:
#             instance = self.get_object()
#             update_bg_order_task.delay(order_id=str(instance.id))

#         return response

#     @extend_schema(
#         summary='Отменить фоновый заказ',
#         description=(
#             'Отмена фонового заказа.\n\n'
#             'Заказ помечается статусом "Отменён" (3), '
#             'и создаётся репликация отмены для отправки на клиент.\n\n'
#             'Отменить можно только заказы со статусами 0 (Ожидает) или 1 (В эфире).'
#         ),
#         examples=[
#             OpenApiExample(
#                 'Успешно отменен',
#                 value={'message': 'Запрос на отмену заказа принят.'},
#                 status_codes=[HTTP_200_OK],
#                 response_only=True
#             ),
#             OpenApiExample(
#                 'Пользователь неавторизован',
#                 value={'detail': 'Учетные данные не были предоставлены.'},
#                 status_codes=[HTTP_401_UNAUTHORIZED],
#                 response_only=True
#             )
#         ],
#         responses={
#             HTTP_200_OK: DetailSerializer,
#             HTTP_401_UNAUTHORIZED: DetailSerializer,
#         }
#     )
#     @action(detail=True, methods=['DELETE'])
#     def cancel(self, request, pk):
#         """
#         Отмена заказа.

#         Args:
#             request: HTTP запрос.
#             pk (str): UUID заказа.

#         Returns:
#             Response: Сообщение о принятии запроса на отмену.
#         """
#         cancel_bg_order_task.delay(str(pk))
#         return Response(
#             data={'message': 'Запрос на отмену заказа принят.'},
#             status=HTTP_200_OK
#         )

#     def get_serializer(self, *args, **kwargs):
#         """
#         Выбор сериализатора в зависимости от действия.

#         Для списка (list) используется BgOrderListSerializer (сжатый формат).
#         Для остальных действий — BgOrderSerializer (полный формат).
#         """
#         if self.action == 'list':
#             serializer_class = BgOrderListSerializer
#         else:
#             serializer_class = BgOrderSerializer

#         # Если передан список данных — включаем many=True
#         if 'data' in kwargs:
#             data = kwargs['data']
#             if isinstance(data, list):
#                 kwargs['many'] = True

#         return serializer_class(*args, **kwargs)


# # from django_filters.rest_framework import DjangoFilterBackend
# # from drf_spectacular.utils import (
# #     extend_schema,
# #     extend_schema_view,
# #     OpenApiExample
# # )
# # from rest_framework import viewsets, mixins
# # from rest_framework.decorators import action
# # from rest_framework.response import Response
# # from rest_framework.status import (
# #     HTTP_200_OK,
# #     HTTP_201_CREATED,
# #     HTTP_401_UNAUTHORIZED,
# #     HTTP_405_METHOD_NOT_ALLOWED,
# #     HTTP_404_NOT_FOUND,
# #     HTTP_400_BAD_REQUEST
# # )

# # from api.constants import (
# #     restricted_update,
# #     DetailSerializer,
# #     DEFAULT_SCHEMA_RESPONSES,
# #     DEFAULT_SCHEMA_EXAMPLES
# # )
# # from orders.filters import AdOrderFilter, BgOrderFilter
# # from orders.serializers import (
# #     AdOrderSerializer,
# #     AdOrderListSerializer,
# #     BgOrderSerializer,
# #     BgOrderListSerializer
# # )
# # from orders.models import AdOrder, BgOrder
# # from orders.tasks import (
# #     create_ad_order_task,
# #     update_ad_order_task,
# #     cancel_ad_order_task,
# #     create_bg_order_task,
# #     update_bg_order_task,
# #     cancel_bg_order_task
# # )
# # from users.permissions import StaffCUDAuthRetrieve


# # class NoDeleteViewSet(
# #     mixins.CreateModelMixin, mixins.RetrieveModelMixin,
# #     mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
# # ):
# #     """Вьюсет без поддержки метода DELETE."""


# # @extend_schema_view(
# #     partial_update=extend_schema(
# #         summary='Обновить рекламный заказ',
# #         examples=DEFAULT_SCHEMA_EXAMPLES + [
# #             OpenApiExample(
# #                 'Данные для обновления заказа со слайдами.',
# #                 value={
# #                     'name': 'Иное название заказа',
# #                     'description': 'Иное описание заказа',
# #                     'playlist': '40e6215d-b5c6-4896-987c-f30f3678f608',
# #                     'slides': {
# #                         '6ecd8c99-4036-403d-bf84-cf8400f67836': [
# #                             '3f333df6-90a4-4fda-8dd3-9485d27cee36'
# #                         ]
# #                     }
# #                 },
# #                 request_only=True
# #             ),
# #             OpenApiExample(
# #                 'Запрещенное поле для обновления',
# #                 value={'detail': 'Нельзя обновить поля: status'},
# #                 status_codes=[HTTP_400_BAD_REQUEST],
# #                 response_only=True
# #             )
# #         ],
# #         responses={HTTP_200_OK: AdOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
# #     ),
# #     list=extend_schema(
# #         summary='Получить пагинированный список заказов',
# #         responses={
# #             HTTP_200_OK: AdOrderListSerializer(many=True)
# #         } | DEFAULT_SCHEMA_RESPONSES
# #     ),
# #     retrieve=extend_schema(
# #         summary='Получить расшифровку заказа',
# #         examples=[
# #             OpenApiExample(
# #                 'Заказ с типом 0 (без слайдов)',
# #                 description=(
# #                     'Заказ по режиму работы точки без слайдов, '
# #                     'его время в эфире зависит от настроек номенклатуры.'
# #                 ),
# #                 status_codes=[HTTP_200_OK],
# #                 response_only=True,
# #                 value={
# #                     'id': 'e3d9f55e-8504-498d-900c-0a48cd27fbdb',
# #                     'name': 'Наименование заказа с типом 0',
# #                     'description': (
# #                         'Текстовое описание заказа, '
# #                         'не является обязательным полем.'
# #                     ),
# #                     'owner': {'full_name': 'Фамилия Имя'},
# #                     'playlist': {
# #                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
# #                         'name': 'Наименование плейлиста',
# #                         'files_count': 100500
# #                     },
# #                     'slides': 'null',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 0,
# #                     'parameters': {
# #                         'times_in_hour': 4,
# #                         'weight': 0
# #                     },
# #                     'status': 0,
# #                     'created': '2025-04-28 22:36:04',
# #                     'client': {
# #                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         'name': '!!! #Test 8 Борисов И.'
# #                     }
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 1 (без слайдов)',
# #                 description=(
# #                     'Заказ будет в эфире от начала работы магазина '
# #                     'и проигрываться в течении часа. '
# #                     'Добавляется дополнительный параметр '
# #                     'timedelta - смещение по времени, '
# #                     'от какого времени начнет играть заказ, например 5 минут, '
# #                     'этот параметр не может быть менее минуты.'
# #                 ),
# #                 status_codes=[HTTP_200_OK],
# #                 response_only=True,
# #                 value={
# #                     'id': '88a70e05-ce8e-4b26-8d28-94f9eb59e03b',
# #                     'name': 'Наименование заказа с типом 1',
# #                     'description': 'null',
# #                     'owner': {'full_name': 'Фамилия Имя'},
# #                     'playlist': {
# #                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
# #                         'name': 'Наименование плейлиста',
# #                         'files_count': 1337
# #                     },
# #                     'slides': 'null',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 1,
# #                     'parameters': {
# #                         'times_in_hour': 4,
# #                         'weight': 0,
# #                     "timedelta": [0, 5, 0]
# #                     },
# #                     'status': 0,
# #                     'created': '2025-04-28 22:36:04',
# #                     'client': {
# #                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         'name': '!!! #Test 8 Борисов И.'
# #                     }
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 2 (без слайдов)',
# #                 description=(
# #                     'Заказ с типом 2 будет играть от указанного смещения '
# #                     'по времени до окончания работы точки.'
# #                 ),
# #                 status_codes=[HTTP_200_OK],
# #                 response_only=True,
# #                 value={
# #                     'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
# #                     'name': 'Название заказа с типом 2',
# #                     'owner': {'full_name': 'Фамилия Имя'},
# #                     'description': 'null',
# #                     'playlist': {
# #                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
# #                         'name': 'Наименование плейлиста',
# #                         'files_count': 1337
# #                     },
# #                     'slides': 'null',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 2,
# #                     'parameters': {
# #                         'times_in_hour': 1,
# #                         'weight': 0,
# #                     "timedelta": [0, 30, 0]
# #                     },
# #                     'status': 0,
# #                     'created': '2025-04-28 22:36:04',
# #                     'client': {
# #                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         'name': '!!! #Test 8 Борисов И.'
# #                     }
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 3 (без слайдов)',
# #                 description=(
# #                     'Заказ с типом 3 будет играть от указанного времени '
# #                     'start_time и до указанного времени end_time вне '
# #                     'зависимости от изменений режима работы точки, '
# #                     'но нужно учитывать настройки громкости, '
# #                     'если разместить заказ до начала работы '
# #                     'и не включить звук, то заказ будет без звука.'
# #                 ),
# #                 status_codes=[HTTP_200_OK],
# #                 response_only=True,
# #                 value={
# #                     'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
# #                     'name': 'Название заказа с типом 3',
# #                     'owner': {'full_name': 'Фамилия Имя'},
# #                     'description': 'null',
# #                     'playlist': {
# #                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
# #                         'name': 'Наименование плейлиста',
# #                         'files_count': 420
# #                     },
# #                     'slides': 'null',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 3,
# #                     'parameters': {
# #                         'times_in_hour': 1,
# #                         'start_time': '12:00:00',
# #                         'end_time': '18:00:00',
# #                         'weight': 30,
# #                         "timedelta": [0, 30, 0]
# #                     },
# #                     'status': 0,
# #                     'created': '2025-04-28 22:36:04',
# #                     'client': {
# #                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         'name': '!!! #Test 8 Борисов И.'
# #                     }
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 4 (без слайдов)',
# #                 description=(
# #                     'Заказ с типом 4 будет проигрываться с момента '
# #                     'открытия магазина и до указанного времени end_time.'
# #                 ),
# #                 status_codes=[HTTP_200_OK],
# #                 response_only=True,
# #                 value={
# #                     'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
# #                     'name': 'Название заказа с типом 4',
# #                     'owner': {'full_name': 'Фамилия Имя'},
# #                     'description': 'null',
# #                     'playlist': {
# #                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
# #                         'name': 'Наименование плейлиста',
# #                         'files_count': 420
# #                     },
# #                     'slides': 'null',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 4,
# #                     'parameters': {
# #                         'times_in_hour': 1,
# #                         'end_time': '12:00:00',
# #                         'weight': 30,
# #                         "timedelta": [0, 5, 0]
# #                     },
# #                     'status': 0,
# #                     'created': '2025-04-28 22:36:04',
# #                     'client': {
# #                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         'name': '!!! #Test 8 Борисов И.'
# #                     }
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 5 (без слайдов)',
# #                 description=(
# #                     'Заказ с типом 5 будет проигрываться от '
# #                     'указанного времени start_time '
# #                     'до времени закрытия магазина.'
# #                 ),
# #                 status_codes=[HTTP_200_OK],
# #                 response_only=True,
# #                 value={
# #                     'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
# #                     'name': 'Название заказа с типом 4',
# #                     'owner': {'full_name': 'Фамилия Имя'},
# #                     'description': 'null',
# #                     'playlist': {
# #                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
# #                         'name': 'Наименование плейлиста',
# #                         'files_count': 111
# #                     },
# #                     'slides': 'null',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 5,
# #                     'parameters': {
# #                         'times_in_hour': 1,
# #                         'start_time': '18:00:00',
# #                         'weight': 90,
# #                         "timedelta": [0, 5, 0]
# #                     },
# #                     'status': 0,
# #                     'created': '2025-04-28 22:36:04',
# #                     'client': {
# #                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         'name': '!!! #Test 8 Борисов И.'
# #                     }
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ со слайдами (с типом 0)',
# #                 description=(
# #                     'Пример заказа созаднного со слайдами'
# #                 ),
# #                 status_codes=[HTTP_200_OK],
# #                 response_only=True,
# #                 value={
# #                     'id': 'e932863c-c547-4f87-bbb5-39e10b893ad4',
# #                     'name': 'Название заказа с типом 0',
# #                     'owner': {'full_name': 'Фамилия Имя'},
# #                     'description': 'null',
# #                     'playlist': {
# #                         'id': '57c42879-2a80-4304-9551-1c02011f559b',
# #                         'name': 'Наименование плейлиста',
# #                         'files_count': 420
# #                     },
# #                     'slides': {
# #                         'd3c90f33-af4f-496b-ac3d-50db3d72a8c0': [
# #                             'af789a1a-7489-490a-9a80-af4576adad7b', 'ceaf3dcc-7475-4088-ba11-a92eb35d0f1d'
# #                         ]
# #                     },
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 0,
# #                     'parameters': {
# #                         'times_in_hour': 1,
# #                         'weight': 50,
# #                     },
# #                     'status': 0,
# #                     'created': '2025-04-28 22:36:04',
# #                     'client': {
# #                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         'name': '!!! #Test 8 Борисов И.'
# #                     }
# #                 }
# #             )
# #         ],
# #         responses={HTTP_200_OK: AdOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
# #     ),
# #     create=extend_schema(
# #         summary='Создать новый заказ',
# #         request=AdOrderSerializer,
# #         examples=[
# #             OpenApiExample(
# #                 'Заказ с типом 0 (вариант 1)',
# #                 description=(
# #                     'Заказ с типом 0, на одну номенклатуру, '
# #                     'без слайдов, 4 выхода в час без указания приоритета.'
# #                     'Приоритет (вес) заказа по умолчанию ставится 50.'
# #                 ),
# #                 request_only=True,
# #                 value={
# #                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
# #                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
# #                     'name': 'Наименование заказа',
# #                     'description': 'Не обязательно заполнять',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 0,
# #                     'parameters': {'times_in_hour': 4}
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 0 (вариант 2)',
# #                 request_only=True,
# #                 description=(
# #                     'Заказ с типом 0, на несколько номенклатур, '
# #                     'без слайдов, 4 выхода в час без указания приоритета.'
# #                     'Приоритет (вес) заказа по умолчанию ставится 50.'
# #                 ),
# #                 value={
# #                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
# #                     'clients': [
# #                         'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         '163280f9-f40d-4d08-ac57-5fa2e63f479d',
# #                         'e6a58506-d03a-4880-923c-011490b03f96'
# #                     ],
# #                     'name': 'Наименование заказа',
# #                     'description': 'Но заполнить его будет полезно на будущее',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 0,
# #                     'parameters': {'times_in_hour': 4}
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 0 (вариант 3)',
# #                 request_only=True,
# #                 description=(
# #                     'Заказ с типом 0, на несколько номенклатур, '
# #                     'без слайдов, 4 выхода в час с высоким приоритетом.'
# #                 ),
# #                 value={
# #                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
# #                     'clients': [
# #                         'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         '163280f9-f40d-4d08-ac57-5fa2e63f479d',
# #                         'e6a58506-d03a-4880-923c-011490b03f96'
# #                     ],
# #                     'name': 'Наименование заказа',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 0,
# #                     'parameters': {'times_in_hour': 4, 'weight': 90}
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 0 (вариант 4)',
# #                 request_only=True,
# #                 description=(
# #                     'Заказ с типом 0, на несколько номенклатур, '
# #                     'без слайдов, 4 выхода в час с низким приоритетом.'
# #                 ),
# #                 value={
# #                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
# #                     'clients': [
# #                         'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         '163280f9-f40d-4d08-ac57-5fa2e63f479d',
# #                         'e6a58506-d03a-4880-923c-011490b03f96'
# #                     ],
# #                     'name': 'Наименование заказа',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 0,
# #                     'parameters': {'times_in_hour': 4, 'weight': 10}
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 0 (вариант 5)',
# #                 description=(
# #                     'Заказ с типом 0, на одну номенклатуру, '
# #                     'со слайдами, 4 выхода в час без указания приоритета.'
# #                     'Приоритет (вес) заказа по умолчанию ставится 50.'
# #                 ),
# #                 request_only=True,
# #                 value={
# #                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
# #                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
# #                     'name': 'Наименование заказа',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'slides': {
# #                         'd3c90f33-af4f-496b-ac3d-50db3d72a8c0': [
# #                             'af789a1a-7489-490a-9a80-af4576adad7b',
# #                             'ceaf3dcc-7475-4088-ba11-a92eb35d0f1d'
# #                         ]
# #                     },
# #                     'broadcast_type': 0,
# #                     'parameters': {'times_in_hour': 4}
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 1',
# #                 description=(
# #                     'Заказ с типом 1 от начала работы + смещение по времени.'
# #                 ),
# #                 request_only=True,
# #                 value={
# #                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
# #                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
# #                     'name': 'Наименование заказа',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 1,
# #                     'parameters': {'times_in_hour': 1, 'timedelta': '00:05:00'}
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 2',
# #                 description=(
# #                     'Заказ с типом 2 от смещения по времени '
# #                     'до окончания работы точки.'
# #                 ),
# #                 request_only=True,
# #                 value={
# #                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
# #                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
# #                     'name': 'Наименование заказа',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 2,
# #                     'parameters': {'times_in_hour': 4, 'timedelta': '00:45:00'}
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 3',
# #                 description=(
# #                     'Заказ с типом 3 от указанного времени '
# #                     'и до указанного времени.'
# #                 ),
# #                 request_only=True,
# #                 value={
# #                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
# #                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
# #                     'name': 'Наименование заказа',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 3,
# #                     'parameters': {
# #                         'times_in_hour': 4,
# #                         'start_time': '12:00:00',
# #                         'end_time': '18:00:00'
# #                     }
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 4',
# #                 description=(
# #                     'Заказ с типом 4 от открытия точки '
# #                     'и до указанного времени.'
# #                 ),
# #                 request_only=True,
# #                 value={
# #                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
# #                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
# #                     'name': 'Наименование заказа',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 4,
# #                     'parameters': {
# #                         'times_in_hour': 4,
# #                         'end_time': '12:00:00'
# #                     }
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 5',
# #                 description=(
# #                     'Заказ с типом 4 от указанного времени '
# #                     'и до закрытия точки.'
# #                 ),
# #                 request_only=True,
# #                 value={
# #                     'playlist': '57c42879-2a80-4304-9551-1c02011f559b',
# #                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
# #                     'name': 'Наименование заказа',
# #                     'broadcast_interval': {
# #                         'lower': '2025-04-28 09:00:00',
# #                         'upper': '2025-05-01 18:00:00'
# #                     },
# #                     'broadcast_type': 5,
# #                     'parameters': {
# #                         'times_in_hour': 4,
# #                         'start_time': '18:00:00'
# #                     }
# #                 }
# #             )
# #         ],
# #         responses={
# #             HTTP_201_CREATED: AdOrderSerializer
# #         } | DEFAULT_SCHEMA_RESPONSES
# #     )
# # )
# # @extend_schema(tags=['AD Orders'])
# # class AdOrderViewSet(NoDeleteViewSet):
# #     """
# #     # Рекламные заказы.

# #     ## Типы вещания `broadcast_type`
# #     - `0` по режиму работы точки
# #     - `1` от начала работы точки + смещение по времени delta
# #     - `2` от смещения по времени delta до окончания работы точки
# #     - `3` по конкретному вермени
# #     - `4` от начала работы точки до фиксированного времени
# #     - `5` от фиксированного времени до окончания работы точки
# #     - `6` старт вещания по событию

# #     ## Статусы заказов `status`
# #     - `0` Ожидает эфира
# #     - `1` В эфире
# #     - `2` Завершен
# #     - `3` Отменен
# #     - `4` Ошибка

# #     ## Параметры `parameters`
# #     - `weight` приоритет заказа, от 0 более низкий до 100 более высокий
# #     - `times_in_hour` количество выходов в час
# #     - `timedelta` смещение по времени используется для выбора рекламного
# #     блока (сдвиг по минутам), не может превышать 59 минут
# #     - `start_time` и `end_time` используется в некоторых типах для указания
# #     конкретных часов вещания заказа

# #     ## Наименование `name`
# #     - Строковое поле для дальнейшего поиска этого заказа
# #     - Максимальная длинна строки 255 символов

# #     ## Описание `description`
# #     - Не обязательное поле, при желании туда можно написать текст любой длинны

# #     ## Дата создания `created`
# #     - Дата и время когда был создан заказ

# #     ## Интервал работы заказа `broadcast_interval`
# #     - Поле карты с 2 обязательными параметрами `lower` и `apper`
# #         - `lower` Дата и время старта вещания по данному заказу
# #         - `upper` Дата и время окончания вещания по данному закзу

# #     ## Слайды `slides`
# #     - Поле карты которое составляет соответствие трека со слайдами (см пример)

# #     ---

# #     ### Примечание
# #     В скором времени репрезентация parameters
# #     будет исправлена в читаемый вид
# #     """

# #     queryset = AdOrder.objects.all().select_related(
# #         'owner', 'client', 'playlist'
# #     )
# #     filter_backends = [DjangoFilterBackend]
# #     filterset_class = AdOrderFilter
# #     permission_classes = [StaffCUDAuthRetrieve]
# #     http_method_names = ['get', 'post', 'patch', 'delete']

# #     def perform_create(self, serializer):
# #         """
# #         Создание заказов.

# #         0. Получаем данные из сериализатора.
# #         1. Сохраняем заказы, владельца берём из запроса.
# #         2. Собираем айди заказов.
# #         3. Передаём список айди в целери для создания репликаций в фоне.
# #         """
# #         # 0
# #         serializer.is_valid(raise_exception=True)
# #         # 1
# #         orders_list = serializer.save(owner=self.request.user)
# #         orders_ids = []
# #         # 2
# #         for orders in orders_list:
# #             orders_ids.append(
# #                 [str(order.id) for order in orders]
# #                 if len(orders) > 1 else str(orders[0].id)
# #             )
# #         # 3
# #         create_ad_order_task.delay(orders_ids)

# #     def update(self, request, *args, **kwargs):
# #         error_message = (
# #             'Изменить можно только название, описание, '
# #             'плейлист и слайды. Лишние ключи: {keys}.'
# #         )
# #         updatable_fields = (
# #             'name',
# #             'description',
# #             'playlist',
# #             'slides'
# #         )
# #         kwargs.update(updatable_fields=updatable_fields,
# #                       error_message=error_message)
# #         response = restricted_update(self, request, *args, **kwargs)
# #         if 'playlist' in request.data or 'slides' in request.data:
# #             instance = self.get_object()
# #             update_ad_order_task.delay(order_id=str(instance.id))
# #         return response

# #     @extend_schema(
# #         summary='Отменить рекламный заказ',
# #         examples=[
# #             OpenApiExample(
# #                 'Успешно отменен',
# #                 value={'message': 'Запрос на отмену заказа принят.'},
# #                 status_codes=[HTTP_200_OK]
# #             ),
# #             OpenApiExample(
# #                 'Пользователь неавторизован',
# #                 value={'detail': 'Учетные данные не были предоставлены.'},
# #                 status_codes=[HTTP_401_UNAUTHORIZED]
# #             )
# #         ],
# #         responses={HTTP_200_OK: {'body': {}}} | DEFAULT_SCHEMA_RESPONSES
# #     )
# #     @action(detail=True, methods=['DELETE'])
# #     def cancel(self, request, pk):
# #         """Отмена заказа."""
# #         cancel_ad_order_task.delay(str(pk))
# #         return Response(
# #             data={'message': 'Запрос на отмену заказа принят.'},
# #             status=HTTP_200_OK
# #         )

# #     def get_serializer(self, *args, **kwargs):
# #         if self.action == 'list':
# #             serializer = AdOrderListSerializer
# #         else:
# #             serializer = AdOrderSerializer
# #         if 'data' in kwargs:
# #             data = kwargs['data']

# #             if isinstance(data, list):
# #                 kwargs['many'] = True

# #         return serializer(*args, **kwargs)


# # @extend_schema_view(
# #     partial_update=extend_schema(
# #         summary='Обновить фоновый заказ',
# #         examples=[
# #             OpenApiExample(
# #                 name='Поля для обновления',
# #                 value={
# #                     'name': 'Иное название заказа',
# #                     'description': 'Иное описание заказа',
# #                     'playlist': '40e6215d-b5c6-4896-987c-f30f3678f608'
# #                 },
# #                 request_only=True
# #             ),
# #             OpenApiExample(
# #                 'Запрещенное поле для обновления',
# #                 value={'detail': 'Нельзя обновить поля: status'},
# #                 status_codes=[HTTP_400_BAD_REQUEST],
# #                 response_only=True
# #             )
# #         ],
# #         responses={HTTP_200_OK: BgOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
# #     ),
# #     list=extend_schema(
# #         summary='Получить пагинированный список фоновых заказов',
# #         responses={
# #                       HTTP_200_OK: BgOrderListSerializer(many=True)
# #                   } | DEFAULT_SCHEMA_RESPONSES
# #     ),
# #     retrieve=extend_schema(
# #         summary='Получить расшифровку фонового заказа',
# #         examples=[
# #             OpenApiExample(
# #                 'Заказ с типом 0 (фоновая музыка)',
# #                 response_only=True,
# #                 description='Заказ фоновой музыки который еще не находится в эфире',
# #                 value={
# #                     'id': '0fc26d0e-6a12-4481-8edf-dfdbd374c3e6',
# #                     'name': 'Наименование заказа фоновой музыки',
# #                     'description': 'Описание заказа (опционально)',
# #                     'owner': {'full_name': 'Фамилия Имя'},
# #                     'order_type': 0,
# #                     'playlist': {
# #                         'id': '3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c',
# #                         'name': 'Плейлист фоновой музыки',
# #                         'files_count': 1337
# #                     },
# #                     'broadcast_interval': {
# #                         'lower': '2025-05-05 09:00:00',
# #                         'upper': '2025-05-11 18:00:00'
# #                     },
# #                     'parameters': {},
# #                     'status': 0,
# #                     'created': '2025-05-03 23:08:01',
# #                     'client': {
# #                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         'name': '!!! #Test 8 Борисов И.'
# #                     }
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 1 (Фоновые видео)',
# #                 response_only=True,
# #                 description='Заказ фоновых видео, эфир которого уже завершился',
# #                 value={
# #                     'id': '97196f20-2cd0-4416-9d29-147b03b48b5e',
# #                     'name': 'Наименование заказа фоновых видео',
# #                     'owner': {'full_name': 'Фамилия Имя'},
# #                     'order_type': 1,
# #                     'playlist': {
# #                         'id': 'a66f3388-6b84-4513-99e5-f47c64bd9ef4',
# #                         'name': 'Плейлист видео',
# #                         'files_count': 42
# #                     },
# #                     'broadcast_interval': {
# #                         'lower': '2025-03-07 08:00:00',
# #                         'upper': '2025-03-07 19:00:00'
# #                     },
# #                     'parameters': {},
# #                     'status': 2,
# #                     'created': '2025-03-06 23:08:01',
# #                     'client': {
# #                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         'name': '!!! #Test 8 Борисов И.'
# #                     }
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Заказ с типом 2 (Фоновые картинки)',
# #                 response_only=True,
# #                 description='Заказ фоновых картинок который был ранее отменен',
# #                 value={
# #                     'id': '188edfd8-83f7-4dc2-917e-248ef6f56c77',
# #                     'name': 'Наименование заказа фоновых картинок',
# #                     'owner': {'full_name': 'Фамилия Имя'},
# #                     'order_type': 2,
# #                     'playlist': {
# #                         'id': '18936ac7-702c-4c9c-be2e-580f9b163016',
# #                         'name': 'Плейлист картинок',
# #                         'files_count': 127
# #                     },
# #                     'broadcast_interval': {
# #                         'lower': '2025-03-07 08:00:00',
# #                         'upper': '2025-03-07 19:00:00'
# #                     },
# #                     'parameters': {},
# #                     'status': 3,
# #                     'created': '2025-03-06 23:08:01',
# #                     'client': {
# #                         'id': 'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         'name': '!!! #Test 8 Борисов И.'
# #                     }
# #                 }
# #             )
# #         ],
# #         responses={HTTP_200_OK: BgOrderSerializer} | DEFAULT_SCHEMA_RESPONSES
# #     ),
# #     create=extend_schema(
# #         summary='Создать фоновый заказ',
# #         request=BgOrderSerializer,
# #         examples=[
# #             OpenApiExample(
# #                 'Создать заказ фоновой музыки на 1 номенклатуру',
# #                 request_only=True,
# #                 description='Пример данных для создания заказа фоновой музыки на одну номенклатуру',
# #                 value={
# #                     'playlist': '3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c',
# #                     'clients': ['d6578da7-50e0-49f4-81bd-eba08474b950'],
# #                     'name': 'Заказ фоновой музыки на 1 номенклатуру',
# #                     'description': 'Создано для примера',
# #                     'broadcast_interval': {
# #                         'lower': '2025-05-05 09:00:00',
# #                         'upper': '2025-05-11 18:00:00'
# #                     },
# #                     'parameters': {},
# #                     'order_type': 0
# #                 }
# #             ),
# #             OpenApiExample(
# #                 'Создать заказ фоновой музыки на несколько номенклатур',
# #                 request_only=True,
# #                 description='Пример данных для создания заказа фоновой музыки на 3 номенклатуры',
# #                 value={
# #                     'playlist': '3d29a71c-1cfc-4f4b-8f90-3d736bf15f6c',
# #                     'clients': [
# #                         'd6578da7-50e0-49f4-81bd-eba08474b950',
# #                         '163280f9-f40d-4d08-ac57-5fa2e63f479d',
# #                         'e6a58506-d03a-4880-923c-011490b03f96'
# #                     ],
# #                     'name': 'Заказ фоновой музыки на несколько номенклатур',
# #                     'description': 'Создано для примера',
# #                     'broadcast_interval': {
# #                         'lower': '2025-05-05 09:00:00',
# #                         'upper': '2025-05-11 18:00:00'
# #                     },
# #                     'parameters': {},
# #                     'order_type': 0
# #                 }
# #             )
# #         ]
# #     )
# # )
# # @extend_schema(tags=['BG Orders'])
# # class BgOrderViewSet(NoDeleteViewSet):
# #     """
# #     # Фоновые заказы.

# #     ## Типы фоновых заказов `order_type`
# #     - `0` Фоновая музыка
# #     - `1` Фоновые Видео
# #     - `2` Фоновые картинки
# #     - `3` Бегущая строка

# #     ## Статусы заказов `status`
# #     - `0` Ожидает эфира
# #     - `1` В эфире
# #     - `2` Завершен
# #     - `3` Отменен
# #     - `4` Ошибка

# #     ## Плейлист `playlist`
# #     - Тип контента плейлиста должен совпадать с типом заказа при его создании
# #     - Указывается уид `id` плейлиста

# #     ## Наименование `name`
# #     - Строковое поле для дальнейшего поиска этого заказа
# #     - Максимальная длинна строки 255 символов

# #     ## Описание `description`
# #     - Не обязательное поле, при желании туда можно написать текст любой длинны

# #     ## Интервал работы заказа `broadcast_interval`
# #     - Поле карты с 2 обязательными параметрами `lower` и `apper`
# #         - `lower` Дата и время старта вещания по данному заказу
# #         - `upper` Дата и время окончания вещания по данному закзу

# #     ## Параметры `parameters`
# #     - При создании можно оставить пустой `{}` в дальнейшем
# #     будет прописана логика для более гибкой настройки вещания
# #     """

# #     queryset = BgOrder.objects.all().select_related(
# #         'owner', 'client', 'playlist'
# #     )
# #     filter_backends = [DjangoFilterBackend]
# #     filterset_class = BgOrderFilter
# #     permission_classes = [StaffCUDAuthRetrieve]
# #     http_method_names = ['get', 'post', 'patch', 'delete']

# #     def create(self, request, *args, **kwargs):
# #         """
# #         Создание одного или нескольких фоновых заказов.

# #         Returns:
# #             - При создании одного заказа: один объект (BgOrderSerializer)
# #             - При создании нескольких заказов: список объектов (BgOrderListSerializer)
# #         """
# #         # Валидируем данные
# #         serializer = self.get_serializer(data=request.data)
# #         serializer.is_valid(raise_exception=True)

# #         # Сохраняем заказы - получаем список созданных объектов
# #         orders = serializer.save(owner=self.request.user)

# #         # Запускаем Celery задачу с ID всех созданных заказов
# #         orders_ids = [str(order.id) for order in orders]
# #         create_bg_order_task.delay(orders_ids)

# #         # Сериализуем ответ в зависимости от количества созданных заказов
# #         if len(orders) > 1:
# #             # Для нескольких заказов используем ListSerializer
# #             response_serializer = BgOrderListSerializer(orders, many=True)
# #         else:
# #             # Для одного заказа используем полный сериализатор
# #             response_serializer = BgOrderSerializer(orders[0])

# #         return Response(response_serializer.data, status=HTTP_201_CREATED)

# #     def update(self, request, *args, **kwargs):
# #         error_message = (
# #             'Изменить можно только название, описание и '
# #             'плейлист. Лишние ключи: {keys}.'
# #         )
# #         updatable_fields = (
# #             'name',
# #             'description',
# #             'playlist'
# #         )
# #         kwargs.update(updatable_fields=updatable_fields,
# #                       error_message=error_message)
# #         response = restricted_update(self, request, *args, **kwargs)
# #         if 'playlist' in request.data:
# #             instance = self.get_object()
# #             update_bg_order_task.delay(order_id=str(instance.id))
# #         return response

# #     @extend_schema(
# #         summary='Отменить фоновый заказ',
# #         examples=[
# #             OpenApiExample(
# #                 'Успешно отменен',
# #                 value={'message': 'Запрос на отмену заказа принят.'},
# #                 status_codes=[HTTP_200_OK],
# #                 response_only=True
# #             ),
# #             OpenApiExample(
# #                 'Пользователь неавторизован',
# #                 value={'detail': 'Учетные данные не были предоставлены.'},
# #                 status_codes=[HTTP_401_UNAUTHORIZED],
# #                 response_only=True
# #             )
# #         ],
# #         responses={
# #             HTTP_200_OK: DetailSerializer,
# #             HTTP_401_UNAUTHORIZED: DetailSerializer,
# #         }
# #     )
# #     @action(detail=True, methods=['DELETE'])
# #     def cancel(self, request, pk):
# #         """Отмена заказа."""
# #         cancel_bg_order_task.delay(str(pk))
# #         return Response(
# #             data={'message': 'Запрос на отмену заказа принят.'},
# #             status=HTTP_200_OK
# #         )

# #     def get_serializer(self, *args, **kwargs):
# #         if self.action == 'list':
# #             serializer = BgOrderListSerializer
# #         else:
# #             serializer = BgOrderSerializer
# #         if 'data' in kwargs:
# #             data = kwargs['data']

# #             if isinstance(data, list):
# #                 kwargs['many'] = True

# #         return serializer(*args, **kwargs)
