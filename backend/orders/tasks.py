from datetime import datetime as dt

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
    ON_AIR = 1
    COMPLETED = 2

    for order in waiting_adorders:
        order_start = order.broadcast_interval.lower
        if order_start <= dt.now():
            order.status = ON_AIR
            adorders_started.append(order)
    count += len(adorders_started)
    AdOrder.objects.bulk_update(adorders_started, fields=['status'])

    for order in ending_adorders:
        order_end = order.broadcast_interval.upper
        if order_end <= dt.now():
            order.status = COMPLETED
            adorders_ended.append(order)
    count += len(adorders_ended)
    AdOrder.objects.bulk_update(adorders_ended, fields=['status'])

    for order in waiting_bgorders:
        order_start = order.broadcast_interval.lower
        if order_start <= dt.now():
            order.status = ON_AIR
            bgorders_started.append(order)
    count += len(bgorders_started)
    BgOrder.objects.bulk_update(bgorders_started, fields=['status'])

    for order in ending_bgorders:
        order_end = order.broadcast_interval.upper
        if order_end <= dt.now():
            order.status = COMPLETED
            bgorders_ended.append(order)
    count += len(bgorders_ended)
    BgOrder.objects.bulk_update(bgorders_ended, fields=['status'])

    return f"Обновлено {count} статусов заказов."


@shared_task
def create_ad_order_task(orders_ids: list):
    """
    Отправка рекламного заказа.

    0. Фильтруем заказы по полученному списку.
    1. Проходим по получившемуся списку.
    2. Заполняем список репликаций на отмену, берём нужную инфу с заказа.
    3. Создаём все репликации одной операцией, фиксируем количество.
    """
    task_list = []
    AD = 4
    # 0
    orders = AdOrder.objects.filter(pk__in=orders_ids)
    # 1
    for order in orders:
        # 2
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=AD,
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
    # 3
    Task.objects.bulk_create(task_list)
    result = f'Отправленно заказов: {len(task_list)}.'
    return result


@shared_task
def cancel_ad_order_task(order_ids: list):
    """
    Отмена рекламного заказа.

    0. Фильтруем заказы по полученному списку.
    1. Проходим по получившемуся списку.
    2. Заполняем список репликаций на отмену, берём нужную инфу с заказа.
    3. Меняем статус заказу.
    4. Создаём все репликации одной операцией, фиксируем количество.
    """
    task_list = []
    CANCEL = 3
    CANCEL_AD = 9
    # 0
    orders = AdOrder.objects.filter(pk__in=order_ids)
    # 1
    for order in orders:
        # 2
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=CANCEL_AD,
                parameters={'order_id': str(order.id)}
            )
        )
        # 3
        order.status = CANCEL
        order.save()
    # 4
    Task.objects.bulk_create(task_list)
    result = f'Отменено заказов: {len(task_list)}.'
    return result


@shared_task
def create_bg_order_task(orders_ids: list):
    """
    Отправка фонового заказа.

    0. Фильтруем заказы по полученному списку.
    1. Проходим по получившемуся списку.
    2. Заполняем список репликаций на отмену, берём нужную инфу с заказа.
    3. Создаём все репликации одной операцией, фиксируем количество.
    """
    # 0
    orders = BgOrder.objects.filter(pk__in=orders_ids)
    task_list = []
    # 1
    for order in orders:
        # 2
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
    # 3
    Task.objects.bulk_create(task_list)
    result = f'Создано заказов: {len(task_list)}.'
    return result


@shared_task
def cancel_bg_order_task(order_ids: list):
    """
    Отмена фонового заказа.

    0. Фильтруем заказы по полученному списку.
    1. Проходим по получившемуся списку.
    2. Подставляем правильный тип репликации, в зависимости от типа заказа.
    3. Заполняем список репликаций на отмену, берём нужную инфу с заказа.
    4. Меняем статус заказу.
    5. Создаём все репликации одной операцией, фиксируем количество.
    """
    from api.constants import Constants
    task_list = []
    CANCEL = 3
    # 0
    orders = BgOrder.objects.filter(pk__in=order_ids)
    # 1
    for order in orders:
        # 2
        task_type = Constants.get_task_type(order.order_type)
        # 3
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=task_type,
                parameters={'order_id': str(order.id)}
            )
        )
        # 4
        order.status = CANCEL
        order.save()
    # 5
    Task.objects.bulk_create(task_list)
    result = f'Отменено заказов: {len(task_list)}.'
    return result
