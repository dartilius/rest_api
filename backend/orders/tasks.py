from datetime import datetime as dt
from django.core import serializers

from celery import shared_task
from celery_singleton import Singleton

from api.logger import setup_logger
from orders.models import AdOrder, BgOrder
from tasks.models import Task

ad_logger = setup_logger('ad_orders', 'logs/ad_orders.log')
bg_logger = setup_logger('bg_orders', 'logs/bg_orders.log')


@shared_task(base=Singleton)
def update_order_status():
    """
    Обновление статусов доступности номенклатур
    и запись истории их изменения.
    """
    waiting_adorders = AdOrder.objects.filter(status=0)
    waiting_bgorders = BgOrder.objects.filter(status=0)
    ending_adorders = AdOrder.objects.filter(status=1)
    ending_bgorders = BgOrder.objects.filter(status=1)
    adorders_started = []
    bgorders_started = []
    adorders_ended = []
    bgorders_ended = []
    count = 0

    for order in waiting_adorders:
        order_start = order.broadcast_interval.lower
        if order_start <= dt.now():
            order.status = 1
            adorders_started.append(order)
    count += len(adorders_started)
    AdOrder.objects.bulk_update(adorders_started, fields=['status'])

    for order in ending_adorders:
        order_end = order.broadcast_interval.upper
        if order_end <= dt.now():
            order.status = 2
            adorders_ended.append(order)
    count += len(adorders_ended)
    AdOrder.objects.bulk_update(adorders_ended, fields=['status'])

    for order in waiting_bgorders:
        order_start = order.broadcast_interval.lower
        if order_start <= dt.now():
            order.status = 1
            bgorders_started.append(order)
    count += len(bgorders_started)
    BgOrder.objects.bulk_update(bgorders_started, fields=['status'])

    for order in ending_bgorders:
        order_end = order.broadcast_interval.upper
        if order_end <= dt.now():
            order.status = 2
            bgorders_ended.append(order)
    count += len(bgorders_ended)
    BgOrder.objects.bulk_update(bgorders_ended, fields=['status'])

    return f"Обновлено {count} статусов заказов."


@shared_task
def create_ad_order_task(orders_ids: list):
    """
    Отправка рекламного заказа.

    0. Фильтруем список всех заказов по списку айди.
    1. Собираем инфу для создания репликации.
    1.1. Получаем список клиентов данного заказа.
    1.2. Собираем список репликаций, с параметрами, описывающими
        свойства заказа, такими как айди, интервал вещания и т.д.
    2. Пытаемся создать все репликации одной операцией.
    2.1. В случае успеха фиксируем кол-во созданных репликаций.
    2.2. В случае неудачи фиксируем кол-во неудачных репликаций.
    3. Возвращаем ответ со списком удачных и, если есть, неудачных репликаций.
    """
    orders = AdOrder.objects.filter(pk__in=orders_ids)
    task_list = []

    for order in orders:
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=4,
                parameters={
                    'order_id': str(order.id),
                    'order_parameters': order.parameters,
                    'broadcast_type': order.broadcast_type,
                    'broadcast_interval': f'{order.broadcast_interval.lower}-'
                                          f'{order.broadcast_interval.upper}',
                    'playlist': {
                        'id': str(order.playlist.id),
                        'files': [
                            {
                                'id': str(file.id),
                                'hash': file.hash
                            } for file in order.playlist.files.all()
                        ],
                        'slides': order.slides if order.slides else None
                    }
                }
            )
        )
    Task.objects.bulk_create(task_list)
    result = f'Отправленно заказов: {len(task_list)}.'
    return result


@shared_task
def cancel_ad_order_task(orders_json: dict):
    """
    Отмена рекламного заказа.

    0. Десериализуем пришедший JSON с заказами в объекты.
    1. Тянем с закзов всю нужную для создания репликаций инфу.
    2. Создаём репликации на отмену.
    3. Меняем статус заказу.
    4. Кол-во ошибок фиксируем и возвращаем, а также логгируем с причиной.
    """
    orders = list(serializers.deserialize('json', orders_json))
    task_list = []

    for order in orders:
        order = order.object
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=9,
                parameters={'order_id': str(order.id)}
            )
        )
        order.status = 3
        order.save()
    Task.objects.bulk_create(task_list)
    result = f'Отменено заказов: {len(task_list)}.'
    return result


@shared_task
def create_bg_order_task(orders_ids: list):
    """
    Отправка фонового заказа.

    0. Фильтруем список всех заказов по списку айди.
    1. Собираем инфу для создания репликации.
    1.1. Получаем список клиентов данного заказа.
    1.2. Собираем список репликаций, с параметрами, описывающими
        свойства заказа, такими как айди, интервал вещания и т.д.
    2. Пытаемся создать все репликации одной операцией.
    2.1. В случае успеха фиксируем кол-во созданных репликаций.
    2.2. В случае неудачи фиксируем кол-во неудачных репликаций.
    3. Возвращаем ответ со списком удачных и, если есть, неудачных репликаций.
    """
    orders = BgOrder.objects.filter(pk__in=orders_ids)
    task_list = []

    for order in orders:
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=order.order_type,
                parameters={
                    'order_id': str(order.id),
                    'type': order.order_type,
                    'broadcast_interval': f'{order.broadcast_interval.lower}-'
                                          f'{order.broadcast_interval.upper}',
                    'playlist': {
                        'id': str(order.playlist.id),
                        'files': [
                            {
                                'id': str(file.id),
                                'hash': file.hash
                            } for file in order.playlist.files.all()
                        ]
                    }
                }
            )
        )
    Task.objects.bulk_create(task_list)
    result = f'Создано заказов: {len(task_list)}.'
    return result


@shared_task
def cancel_bg_order_task(orders_json: dict):
    """
    Отмена фонового заказа.

    0. Десериализуем пришедший JSON с заказами в объекты.
    1. Тянем с закзов всю нужную для создания репликаций инфу.
    2. Создаём репликации на отмену.
    3. Меняем статус заказу.
    4. Кол-во ошибок фиксируем и возвращаем, а также логгируем с причиной.
    """
    orders = list(serializers.deserialize('json', orders_json))
    task_list = []

    for order in orders:
        order = order.object
        # order_type -> cancel_{order_type}
        match order.order_type:
            case 0: task_type = 5
            case 1: task_type = 6
            case 2: task_type = 7
            case 3: task_type = 8
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=task_type,
                parameters={'order_id': str(order.id)}
            )
        )
        order.status = 3
        order.save()
    Task.objects.bulk_create(task_list)
    result = f'Отменено заказов: {len(task_list)}.'
    return result
