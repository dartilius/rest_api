from itertools import chain

from celery import shared_task
from celery_singleton import Singleton
from datetime import datetime, timedelta
from django.core import serializers

from nomenclatures.models import NomenclatureAvailability, StatusHistory
from orders.models import AdOrder, BgOrder
from tasks.models import Task


@shared_task(base=Singleton)
def update_nomenclature_status():
    """
    Обновление статусов доступности номенклатур
    и запись истории их изменения.
    """
    statuses = NomenclatureAvailability.objects.all()
    statuses_to_update = []
    status_histories_to_create = []

    for status in statuses:
        now_time = datetime.now()
        new_status = 0
        current_status = status.status
        last_answer = status.last_answer_date
        if current_status == 0:
            if now_time - last_answer > timedelta(hours=1):
                new_status = 2
            elif now_time - last_answer > timedelta(minutes=5):
                new_status = 1
            if new_status != current_status:
                status.status = new_status
                statuses_to_update.append(status)
                status_histories_to_create.append(
                    StatusHistory(
                        status=new_status,
                        client=status.client
                    )
                )

        if current_status == 1:
            new_status = 1
            if now_time - last_answer > timedelta(hours=1):
                new_status = 2
            elif now_time - last_answer < timedelta(minutes=5):
                new_status = 0
            if new_status != current_status:
                status.status = new_status
                statuses_to_update.append(status)
                status_histories_to_create.append(
                    StatusHistory(
                        status=new_status,
                        client=status.client
                    )
                )

        if current_status == 2:
            if now_time - last_answer < timedelta(minutes=5):
                status.status = 0
                statuses_to_update.append(status)
                status_histories_to_create.append(
                    StatusHistory(
                        status=new_status,
                        client=status.client
                    )
                )

    NomenclatureAvailability.objects.bulk_update(statuses_to_update, ['status'])
    StatusHistory.objects.bulk_create(status_histories_to_create)

    return f'Обновлено {len(statuses_to_update)} статусов доступности.'


@shared_task
def resend_orders_task(order_ids: list):
    """
    Переотправка рекламного заказа.

    0. Десериализуем полченные заказы, наполняем ими список.
    1. Проходим по списку заказов. Заполняем параметры репликации,
        в зависимости от типа заказа.
    2. Формируем список репликаций для создания.
    3. Создаём все репликации одной операцией.
    4. Возвращаем ответ со списком созданных репликаций.
    """
    orders = chain(
        AdOrder.objects.filter(id__in=order_ids),
        BgOrder.objects.filter(id__in=order_ids)
    )
    task_list = []

    for order in orders:
        parameters = {
            'order_id': str(order.id),
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
        # если реклама - рекламные параметры, иначе фоновые
        if isinstance(order, AdOrder):
            parameters.update({
                'order_parameters': order.parameters,
                'broadcast_type': order.broadcast_type,
            })
            parameters['playlist']['slides'] = (
                order.slides if order.slides else None
            )
            task_type = 4
        else:
            parameters.update({'type': order.order_type})
            task_type = order.order_type

        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=task_type,
                parameters=parameters
            )
        )
    Task.objects.bulk_create(task_list)
    result = f'Переотправленно заказов: {len(task_list)}.'
    return result
