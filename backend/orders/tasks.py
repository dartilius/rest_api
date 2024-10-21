from datetime import datetime as dt
from celery import shared_task
from celery_singleton import Singleton

from orders.models import AdOrder, BgOrder


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
