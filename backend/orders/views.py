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
    mixins.CreateModelMixin, mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """Вьюсет без поддержки метода DELETE."""


@extend_schema_view(
    partial_update=extend_schema(
        summary='Обновить рекламный заказ',
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
        summary='Получить пагинированный список заказов',
        responses={
            HTTP_200_OK: AdOrderListSerializer(many=True)
        } | DEFAULT_SCHEMA_RESPONSES
    ),
    retrieve=extend_schema(
        summary='Получить расшифровку заказа',
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
                    'description': (
                        'Текстовое описание заказа, '
                        'не является обязательным полем.'
                    ),
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
                    'и проигрываться в течении часа. '
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
                    "timedelta": [0, 5, 0]
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
                    "timedelta": [0, 30, 0]
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
                    'зависимости от изменений режима работы точки, '
                    'но нужно учитывать настройки громкости, '
                    'если разместить заказ до начала работы '
                    'и не включить звук, то заказ будет без звука.'
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
                        "timedelta": [0, 30, 0]
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
                        "timedelta": [0, 5, 0]
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
                    'name': 'Название заказа с типом 4',
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
                        "timedelta": [0, 5, 0]
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
                description=(
                    'Пример заказа созаднного со слайдами'
                ),
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
                            'af789a1a-7489-490a-9a80-af4576adad7b', 'ceaf3dcc-7475-4088-ba11-a92eb35d0f1d'
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
        summary='Создать новый заказ',
        request=AdOrderSerializer,
        examples=[
            OpenApiExample(
                'Заказ с типом 0 (вариант 1)',
                description=(
                    'Заказ с типом 0, на одну номенклатуру, '
                    'без слайдов, 4 выхода в час без указания приоритета.'
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
                request_only=True,
                description=(
                    'Заказ с типом 0, на несколько номенклатур, '
                    'без слайдов, 4 выхода в час без указания приоритета.'
                    'Приоритет (вес) заказа по умолчанию ставится 50.'
                ),
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
                request_only=True,
                description=(
                    'Заказ с типом 0, на несколько номенклатур, '
                    'без слайдов, 4 выхода в час с высоким приоритетом.'
                ),
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
                request_only=True,
                description=(
                    'Заказ с типом 0, на несколько номенклатур, '
                    'без слайдов, 4 выхода в час с низким приоритетом.'
                ),
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
                    'со слайдами, 4 выхода в час без указания приоритета.'
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
                description=(
                    'Заказ с типом 1 от начала работы + смещение по времени.'
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
                    'broadcast_type': 1,
                    'parameters': {'times_in_hour': 1, 'timedelta': '00:05:00'}
                }
            ),
            OpenApiExample(
                'Заказ с типом 2',
                description=(
                    'Заказ с типом 2 от смещения по времени '
                    'до окончания работы точки.'
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
                    'broadcast_type': 2,
                    'parameters': {'times_in_hour': 4, 'timedelta': '00:45:00'}
                }
            ),
            OpenApiExample(
                'Заказ с типом 3',
                description=(
                    'Заказ с типом 3 от указанного времени '
                    'и до указанного времени.'
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
                description=(
                    'Заказ с типом 4 от открытия точки '
                    'и до указанного времени.'
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
                    'broadcast_type': 4,
                    'parameters': {
                        'times_in_hour': 4,
                        'end_time': '12:00:00'
                    }
                }
            ),
            OpenApiExample(
                'Заказ с типом 5',
                description=(
                    'Заказ с типом 4 от указанного времени '
                    'и до закрытия точки.'
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
    # Рекламные заказы.

    ## Типы вещания `broadcast_type`
    - `0` по режиму работы точки
    - `1` от начала работы точки + смещение по времени delta
    - `2` от смещения по времени delta до окончания работы точки
    - `3` по конкретному вермени
    - `4` от начала работы точки до фиксированного времени
    - `5` от фиксированного времени до окончания работы точки
    - `6` старт вещания по событию

    ## Статусы заказов `status`
    - `0` Ожидает эфира
    - `1` В эфире
    - `2` Завершен
    - `3` Отменен
    - `4` Ошибка

    ## Параметры `parameters`
    - `weight` приоритет заказа, от 0 более низкий до 100 более высокий
    - `times_in_hour` количество выходов в час
    - `timedelta` смещение по времени используется для выбора рекламного
    блока (сдвиг по минутам), не может превышать 59 минут
    - `start_time` и `end_time` используется в некоторых типах для указания
    конкретных часов вещания заказа

    ## Наименование `name`
    - Строковое поле для дальнейшего поиска этого заказа
    - Максимальная длинна строки 255 символов

    ## Описание `description`
    - Не обязательное поле, при желании туда можно написать текст любой длинны

    ## Дата создания `created`
    - Дата и время когда был создан заказ

    ## Интервал работы заказа `broadcast_interval`
    - Поле карты с 2 обязательными параметрами `lower` и `apper`
        - `lower` Дата и время старта вещания по данному заказу
        - `upper` Дата и время окончания вещания по данному закзу

    ## Слайды `slides`
    - Поле карты которое составляет соответствие трека со слайдами (см пример)

    ---

    ### Примечание
    В скором времени репрезентация parameters
    будет исправлена в читаемый вид
    """

    queryset = AdOrder.objects.all().select_related(
        'owner', 'client', 'playlist'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdOrderFilter
    permission_classes = [StaffCUDAuthRetrieve]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_create(self, serializer):
        """
        Создание заказов.

        0. Получаем данные из сериализатора.
        1. Сохраняем заказы, владельца берём из запроса.
        2. Собираем айди заказов.
        3. Передаём список айди в целери для создания репликаций в фоне.
        """
        # 0
        serializer.is_valid(raise_exception=True)
        # 1
        orders_list = serializer.save(owner=self.request.user)
        orders_ids = []
        # 2
        for orders in orders_list:
            orders_ids.append(
                [str(order.id) for order in orders]
                if len(orders) > 1 else str(orders[0].id)
            )
        # 3
        create_ad_order_task.delay(orders_ids)

    def update(self, request, *args, **kwargs):
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
        kwargs.update(updatable_fields=updatable_fields,
                      error_message=error_message)
        response = restricted_update(self, request, *args, **kwargs)
        if 'playlist' in request.data or 'slides' in request.data:
            instance = self.get_object()
            update_ad_order_task.delay(order_id=str(instance.id))
        return response

    @extend_schema(
        summary='Отменить рекламный заказ',
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
        """Отмена заказа."""
        cancel_ad_order_task.delay(str(pk))
        return Response(
            data={'message': 'Запрос на отмену заказа принят.'},
            status=HTTP_200_OK
        )

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = AdOrderListSerializer
        else:
            serializer = AdOrderSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)


@extend_schema_view(
    partial_update=extend_schema(
        summary='Обновить фоновый заказ',
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
        responses={
                      HTTP_200_OK: BgOrderListSerializer(many=True)
                  } | DEFAULT_SCHEMA_RESPONSES
    ),
    retrieve=extend_schema(
        summary='Получить расшифровку фонового заказа',
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
        ]
    )
)
@extend_schema(tags=['BG Orders'])
class BgOrderViewSet(NoDeleteViewSet):
    """
    # Фоновые заказы.

    ## Типы фоновых заказов `order_type`
    - `0` Фоновая музыка
    - `1` Фоновые Видео
    - `2` Фоновые картинки
    - `3` Бегущая строка

    ## Статусы заказов `status`
    - `0` Ожидает эфира
    - `1` В эфире
    - `2` Завершен
    - `3` Отменен
    - `4` Ошибка

    ## Плейлист `playlist`
    - Тип контента плейлиста должен совпадать с типом заказа при его создании
    - Указывается уид `id` плейлиста

    ## Наименование `name`
    - Строковое поле для дальнейшего поиска этого заказа
    - Максимальная длинна строки 255 символов

    ## Описание `description`
    - Не обязательное поле, при желании туда можно написать текст любой длинны

    ## Интервал работы заказа `broadcast_interval`
    - Поле карты с 2 обязательными параметрами `lower` и `apper`
        - `lower` Дата и время старта вещания по данному заказу
        - `upper` Дата и время окончания вещания по данному закзу

    ## Параметры `parameters`
    - При создании можно оставить пустой `{}` в дальнейшем
    будет прописана логика для более гибкой настройки вещания
    """

    queryset = BgOrder.objects.all().select_related(
        'owner', 'client', 'playlist'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = BgOrderFilter
    permission_classes = [StaffCUDAuthRetrieve]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def create(self, request, *args, **kwargs):
        """
        Создание одного или нескольких фоновых заказов.

        Returns:
            - При создании одного заказа: один объект (BgOrderSerializer)
            - При создании нескольких заказов: список объектов (BgOrderListSerializer)
        """
        # Валидируем данные
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Сохраняем заказы - получаем список созданных объектов
        orders = serializer.save(owner=self.request.user)

        # Запускаем Celery задачу с ID всех созданных заказов
        orders_ids = [str(order.id) for order in orders]
        create_bg_order_task.delay(orders_ids)

        # Сериализуем ответ в зависимости от количества созданных заказов
        if len(orders) > 1:
            # Для нескольких заказов используем ListSerializer
            response_serializer = BgOrderListSerializer(orders, many=True)
        else:
            # Для одного заказа используем полный сериализатор
            response_serializer = BgOrderSerializer(orders[0])

        return Response(response_serializer.data, status=HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        error_message = (
            'Изменить можно только название, описание и '
            'плейлист. Лишние ключи: {keys}.'
        )
        updatable_fields = (
            'name',
            'description',
            'playlist'
        )
        kwargs.update(updatable_fields=updatable_fields,
                      error_message=error_message)
        response = restricted_update(self, request, *args, **kwargs)
        if 'playlist' in request.data:
            instance = self.get_object()
            update_bg_order_task.delay(order_id=str(instance.id))
        return response

    @extend_schema(
        summary='Отменить фоновый заказ',
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
        """Отмена заказа."""
        cancel_bg_order_task.delay(str(pk))
        return Response(
            data={'message': 'Запрос на отмену заказа принят.'},
            status=HTTP_200_OK
        )

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = BgOrderListSerializer
        else:
            serializer = BgOrderSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)
