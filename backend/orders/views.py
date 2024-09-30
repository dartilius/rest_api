from django.core import serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK
)

from api.constants import Constants
from orders.filters import AdOrderFilter, BgOrderFilter
from orders.serializers import (
    AdOrderSerializer,
    AdOrderListSerializer,
    BgOrderSerializer,
    BgOrderListSerializer
)
from orders.models import AdOrder, BgOrder
from tasks.tasks import (
    create_ad_order_task,
    update_ad_order_task,
    cancel_ad_order_task,
    resend_ad_order_task,
    create_bg_order_task,
    update_bg_order_task,
    cancel_bg_order_task,
    resend_bg_order_task
)


class NoDeleteViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """Вьюсет без предустановленного метода DELETE."""
    pass


class AdOrderViewSet(NoDeleteViewSet):
    """Работа с рекламными заказами."""

    queryset = AdOrder.objects.all().select_related('owner', 'group', 'file')
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdOrderFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        """
        Создание заказов.

        0. Получаем данные из сериализатора.
        1. Сохраняем заказ и ставим ему владельца из запроса.
        2. Собираем айди заказов.
        3. Передаём список айди в целери для создания репликаций в фоне.
        """
        orders = serializer.save(owner=self.request.user)
        orders_ids = [order.id for order in orders]
        create_ad_order_task.delay(orders_ids)

    def perform_update(self, serializer):
        pass
        # data = serializer.data
        # updated_data = {k: v for k, v in data.items() if k != 'id'}
        # orders = serializer.save(update_fields=[*updated_data.keys()])
        # orders_ids = [order.id for order in orders]
        # update_ad_order_task.delay(orders_ids, updated_data)

    @action(methods=['DELETE'], detail=False)
    def cancel(self, request):
        """
        Отмена заказов.

        0. Получаем список заказов на отмену.
        1. Проверяем, что заказы в списке активны.
        1.1. Активные заказы сериализуются в JSON и отправляются в целери
            для отмены и создания соответствующих репликаций в фоне.
        1.2. Заказы, которые нельзя отменить, записываются в отдельный список.
        2. В ответ отдаём сообщение со списком заказов, которые будут отменены
            и которые отменить нельзя.
        """
        cancel_list = request.data['orders']
        orders = AdOrder.objects.filter(pk__in=cancel_list, status__in=[0, 1])
        bad_result = 'Данные заказы невозможно отменить'
        if orders not in Constants.empty_values:
            active_order_ids = [order.id for order in orders]
            orders_json = serializers.serialize('json', orders)
            bad_orders = list(set(cancel_list) - set(active_order_ids))
        else:
            return Response(data=bad_result, status=HTTP_400_BAD_REQUEST)

        cancel_ad_order_task.delay(orders_json)
        return Response(data=f'Запрос на отмену заказов {cancel_list} принят.'
                             f'\n{bad_result}: {bad_orders}',
                        status=HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def resend(self, request):
        """
        Переотправка заказов.

        0. Получаем список заказов на переотпарвку.
        1. Проверяем, что заказы в списке активны.
        1.1. Активные заказы сериализуются в JSON и отправляются в целери
            для создания соответствующих репликаций в фоне.
        1.2. Заказы, которые нельзя переотправить,
            записываем в отдельный список.
        2. В ответ отдаём сообщение со списком заказов, которые будут
            переотправленны и которые переотправить нельзя.
        """
        resend_list = request.data['orders']
        orders = AdOrder.objects.filter(pk__in=resend_list, status__in=[0, 1])
        bad_result = 'Данные заказы невозможно переотправить'
        if orders not in Constants.empty_values:
            active_order_ids = [order.id for order in orders]
            orders_json = serializers.serialize('json', orders)
            bad_orders = list(set(resend_list) - set(active_order_ids))
        else:
            return Response(data=f'{bad_result}: {resend_list}',
                            status=HTTP_400_BAD_REQUEST)

        resend_ad_order_task.delay(orders_json)
        return Response(data=f'Запрос на отмену заказов {resend_list} принят.'
                             f'\n{bad_result}: {bad_orders}',
                        status=HTTP_200_OK)

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


class BgOrderViewSet(NoDeleteViewSet):
    """Работа с фоновыми заказами."""

    queryset = BgOrder.objects.all().select_related(
        'owner', 'group', 'playlist'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = BgOrderFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def perform_create(self, serializer):
        """
        Создание заказов.

        0. Получаем данные из сериализатора.
        1. Сохраняем заказ и ставим ему владельца из запроса.
        2. Собираем айди заказов.
        3. Передаём список айди в целери для создания репликаций в фоне.
        """
        orders = serializer.save(owner=self.request.user)
        orders_ids = [order.id for order in orders]
        create_bg_order_task.delay(orders_ids)

    def perform_update(self, serializer):
        pass
        # data = serializer.data
        # updated_data = {k: v for k, v in data.items() if k != 'id'}
        # order = serializer.save(update_fields=[*updated_data.keys()])
        # update_bg_order_task.delay(order.id, updated_data)

    @action(methods=['DELETE'], detail=False)
    def cancel(self, request):
        """
        Отмена заказов.

        0. Получаем список заказов на отмену.
        1. Проверяем, что заказы в списке активны.
        1.1. Активные заказы сериализуются в JSON и отправляются в целери
            для отмены и создания соответствующих репликаций в фоне.
        1.2. Заказы, которые нельзя отменить, записываем в отдельный список.
        2. В ответ отдаём сообщение со списком заказов, которые будут отменены
            и которые отменить нельзя.
        """
        cancel_list = request.data['orders']
        orders = BgOrder.objects.filter(pk__in=cancel_list, status__in=[0, 1])
        bad_result = 'Данные заказы невозможно отменить'
        if orders not in Constants.empty_values:
            active_order_ids = [order.id for order in orders]
            orders_json = serializers.serialize('json', orders)
            bad_orders = list(set(cancel_list) - set(active_order_ids))
        else:
            return Response(data=f'{bad_result}: {cancel_list}',
                            status=HTTP_400_BAD_REQUEST)

        cancel_bg_order_task.delay(orders_json)
        return Response(data=f'Запрос на отмену заказов {cancel_list} принят.'
                             f'\n{bad_result}: {bad_orders}',
                        status=HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def resend(self, request):
        """
        Переотправка заказов.

        0. Получаем список заказов на переотпарвку.
        1. Проверяем, что заказы в списке активны.
        1.1. Активные заказы сериализуются в JSON и отправляются в celery
            для создания соответствующих репликаций на фоне.
        1.2. Заказы, которые нельзя переотправить,
            записываем в отдельный список.
        2. В ответ отдаём сообщение со списком заказов, которые будут
            переотправленны и которые переотправить нельзя.
        """
        resend_list = request.data['orders']
        orders = BgOrder.objects.filter(pk__in=resend_list, status__in=[0, 1])
        bad_result = 'Данные заказы невозможно переотправить'
        if orders not in Constants.empty_values:
            active_order_ids = [order.id for order in orders]
            orders_json = serializers.serialize('json', orders)
            bad_orders = list(set(resend_list) - set(active_order_ids))
        else:
            return Response(data=f'{bad_result}: {resend_list}',
                            status=HTTP_400_BAD_REQUEST)

        resend_bg_order_task.delay(orders_json)
        return Response(data=f'Запрос на отмену заказов {resend_list} принят.'
                             f'\n{bad_result}: {bad_orders}',
                        status=HTTP_200_OK)

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
