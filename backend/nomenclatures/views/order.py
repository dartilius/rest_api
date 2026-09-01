from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
)

from api.constants import DetailSerializer, get_instance_or_404
from users.permissions import StaffCUDallRead
from ..models import Nomenclature
from ..tasks import resend_orders_task


@extend_schema(tags=["Номенклатуры - Заказы"])
class NomenclatureOrderViewSet(viewsets.ViewSet):
    """
    ViewSet для управления заказами номенклатур.

    Предоставляет методы для переотправки активных заказов (рекламы и фона)
    на номенклатуры. Используется при необходимости синхронизации заказов
    между системой управления и устройствами отображения.

    Endpoints:
        POST /api/orders/{nomenclature_id}/resend_orders/ - Переотправить заказы

    Permissions:
        - resend_orders: IsAuthenticated + IsStaff
    """

    permission_classes = [StaffCUDallRead]

    @extend_schema(
        summary="Переотправить заказы",
        tags=["Номенклатуры", "Заказы"],
        request=None,
        responses={
            HTTP_200_OK: DetailSerializer,
            HTTP_201_CREATED: DetailSerializer,
        },
    )
    @action(detail=True, methods=["POST"])
    def resend_orders(self, request, pk):
        """
        Переотправить активные заказы (реклама и фон) номенклатуры.

        Метод проверяет наличие активных заказов на номенклатуре и, если они есть,
        запускает асинхронную задачу на переотправку этих заказов устройству.
        Это может быть полезно при:
        - Синхронизации данных после сбоя
        - Переотправке потерянных заказов
        - Обновлении конфигурации при изменении плана вещания

        Активные заказы - это заказы со статусом 0 (ожидание отправки) или
        1 (в процессе отправки). Другие статусы (выполнено, ошибка) не переотправляются.

        Args:
            request: HTTP POST запрос.
            pk: UUID номенклатуры.

        Returns:
            Response: JSON с сообщением о результате операции.
                     При отсутствии заказов: {
                         'detail': 'Нет активных заказов.'
                     }
                     При успехе: {
                         'detail': 'Запрос на переотправку заказов принят.'
                     }

        Status Codes:
            200 OK: Нет активных заказов (операция не требуется)
            201 CREATED: Запрос на переотправку принят и отправлен в очередь
            404 NOT FOUND: Номенклатура с таким ID не найдена
            403 FORBIDDEN: Пользователь не имеет прав доступа

        Side Effects:
            - Запускает асинхронную задачу resend_orders_task в Celery очередь
            - Не изменяет статусы заказов сразу (асинхронно)
            - После обработки задачи, заказы будут отправлены на устройство

        Examples:
            >>> # Успешная переотправка
            >>> response = client.post('/api/orders/123e4567-e89b-12d3/resend_orders/')
            >>> response.status_code
            201
            >>> response.data['detail']
            'Запрос на переотправку заказов принят.'

            >>> # Нет активных заказов
            >>> response = client.post('/api/orders/456f7890-a1b2-34cd/resend_orders/')
            >>> response.status_code
            200
            >>> response.data['detail']
            'Нет активных заказов.'

        Performance Notes:
            - Быстрый запрос, работает асинхронно
            - Переотправка выполняется в фоновом потоке (Celery)
            - Не блокирует основной процесс

        Raises:
            HTTP_404_NOT_FOUND: Если номенклатура не существует
        """
        nomenclature = get_instance_or_404(Nomenclature, pk)
        adorders = nomenclature.adorders.filter(status__in=[0, 1]).count()
        bgorders = nomenclature.bgorders.filter(status__in=[0, 1]).count()

        if adorders == 0 and bgorders == 0:
            return Response(
                data={"detail": "Нет активных заказов."}, status=HTTP_200_OK
            )

        resend_orders_task.delay(pk)
        return Response(
            data={"detail": "Запрос на переотправку заказов принят."},
            status=HTTP_201_CREATED,
        )
