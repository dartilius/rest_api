from celery import shared_task
from django.core import serializers

from orders.models import AdOrder, BgOrder
from tasks.models import Task
from api.logger import setup_logger

ad_logger = setup_logger('ad_orders', 'logs/ad_orders.log')
bg_logger = setup_logger('bg_orders', 'logs/bg_orders.log')


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
    successful_tasks = 0
    failed_tasks = 0

    for order in orders:
        clients = order.group.clients.all()
        task_list = [
            Task(
                owner=order.owner,
                client=client,
                type=4,
                parameters={
                    'order_id': order.id,
                    'order_parameters': order.parameters,
                    'broadcast_type': order.broadcast_type,
                    'broadcast_interval': order.broadcast_interval,
                    'file': {
                        'id': str(order.file.id),
                        'hash': order.file.hash,
                        'url': 'placeholder'
                    },
                    'slides': [
                        {
                            'id': str(slide.id),
                            'hash': slide.hash,
                            'url': 'placeholder'
                        } for slide in order.slides.all()
                    ] if order.slides.exists() else None
                }
            ) for client in clients
        ]
        count = len(list(task_list))
        try:
            Task.objects.bulk_create(task_list)
            successful_tasks += count
        except Exception as e:
            # TODO retry
            failed_tasks += count
            ad_logger.error(f'Не удалось отправить {count} '
                            f'заказов: {task_list}.\nОшибка: {e}')

    result = f'Отправленно заказов: {successful_tasks}. '
    if failed_tasks:
        result += f'Ошибки: {failed_tasks}'
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
    successful_tasks = 0
    failed_tasks = 0

    for order in orders:
        order = order.object
        clients = order.group.clients.all()
        task_list = [
            Task(
                owner=order.owner,
                client=client,
                type=9,
                parameters={'order_id': order.id}
            ) for client in clients
        ]
        count = len(list(task_list))
        try:
            Task.objects.bulk_create(task_list)
            order.status = 3
            order.save()
            successful_tasks += count
        except Exception as e:
            # TODO retry
            failed_tasks += count
            ad_logger.error(f'Не удалось отменить {count} '
                            f'заказов: {task_list}.\nОшибка: {repr(e)}')

    result = f'Отменено заказов: {successful_tasks}. '
    if failed_tasks:
        result += f'Ошибки: {failed_tasks}'
    return result


@shared_task
def resend_ad_order_task(orders_json: dict):
    """
    Переотправка рекламного заказа.

    0. Фильтруем список всех заказов по списку айди.
    1. Собираем инфу для создания репликации.
    1.1. Получаем список клиентов данного заказа.
    1.2. Создаём список репликаций, с параметрами, описывающими
        свойства заказа, такими как айди, интервал вещания и т.д.
    2. Пытаемся создать все репликации одной операцией.
    2.1. В случае успеха фиксируем кол-во созданных репликаций.
    2.2. В случае неудачи фиксируем кол-во неудачных репликаций.
    3. Возвращаем ответ со списком удачных и, если есть, неудачных репликаций.
    """
    orders = list(serializers.deserialize('json', orders_json))
    successful_tasks = 0
    failed_tasks = 0

    for order in orders:
        order = order.object
        clients = order.group.clients.all()
        task_list = [
            Task(
                owner=order.owner,
                client=client,
                type=4,
                parameters={
                    'order_id': order.id,
                    'order_parameters': order.parameters,
                    'broadcast_type': order.broadcast_type,
                    'broadcast_interval': order.broadcast_interval,
                    'file': {
                        'id': str(order.file.id),
                        'hash': order.file.hash,
                        'url': 'placeholder'
                    },
                    'slides': [
                        {
                            'id': str(slide.id),
                            'hash': slide.hash,
                            'url': 'placeholder'
                        } for slide in order.slides.all()
                    ] if order.slides.exists() else None
                }
            ) for client in clients
        ]
        count = len(list(task_list))
        try:
            Task.objects.bulk_create(task_list)
            successful_tasks += count
        except Exception as e:
            # TODO retry
            failed_tasks += count
            ad_logger.error(f'Не удалось переотправить {count} '
                            f'заказов: {task_list}.\nОшибка: {e}')

    result = f'Переотправленно заказов: {successful_tasks}. '
    if failed_tasks:
        result += f'Ошибки: {failed_tasks}'
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
    successful_tasks = 0
    failed_tasks = 0

    for order in orders:
        clients = order.group.clients.all()
        task_list = [
            Task(
                owner=order.owner,
                client=client,
                type=order.order_type,
                parameters={
                    'order_id': order.id,
                    'type': order.order_type,
                    'broadcast_interval': order.broadcast_interval,
                    'playlist': [
                        {
                            'id': str(file.id),
                            'hash': file.hash,
                            'url': 'placeholder'
                        } for file in order.playlist.files.all()
                    ]
                }
            ) for client in clients
        ]
        count = len(list(task_list))
        try:
            Task.objects.bulk_create(task_list)
            successful_tasks += count
        except Exception as e:
            # TODO retry
            failed_tasks += count
            bg_logger.error(f'Не удалось создать {count} '
                            f'заказов: {task_list}.\nОшибка: {repr(e)}')

    result = f'Создано заказов: {successful_tasks}. '
    if failed_tasks:
        result += f'Ошибки: {failed_tasks}'
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
    successful_tasks = 0
    failed_tasks = 0

    for order in orders:
        order = order.object
        clients = order.group.clients.all()
        # order_type -> cancel_{order_type}
        match order.order_type:
            case 0: task_type = 5
            case 1: task_type = 6
            case 2: task_type = 7
            case 3: task_type = 8
        task_list = [
            Task(
                owner=order.owner,
                client=client,
                type=task_type,
                parameters={'order_id': order.id}
            ) for client in clients
        ]
        count = len(list(task_list))
        try:
            Task.objects.bulk_create(task_list)
            order.status = 3
            order.save()
            successful_tasks += count
        except Exception as e:
            # TODO retry
            failed_tasks += count
            bg_logger.error(f'Не удалось отменить {count} '
                            f'заказов: {task_list}.\nОшибка: {repr(e)}')

    result = f'Отменено заказов: {successful_tasks}. '
    if failed_tasks:
        result += f'Ошибки: {failed_tasks}'
    return result


@shared_task
def resend_bg_order_task(orders_json: dict):
    """
    Переотправка фонового заказа.

    0. Фильтруем список всех заказов по списку айди.
    1. Собираем инфу для создания репликации.
    1.1. Получаем список клиентов данного заказа.
    1.2. Создаём список репликаций, с параметрами, описывающими
        свойства заказа, такими как айди, интервал вещания и т.д.
    2. Пытаемся создать все репликации одной операцией.
    2.1. В случае успеха фиксируем кол-во созданных репликаций.
    2.2. В случае неудачи фиксируем кол-во неудачных репликаций.
    3. Возвращаем ответ со списком удачных и, если есть, неудачных репликаций.
    """
    orders = list(serializers.deserialize('json', orders_json))
    successful_tasks = 0
    failed_tasks = 0

    for order in orders:
        order = order.object
        clients = order.group.clients.all()
        task_list = [
            Task(
                owner=order.owner,
                client=client,
                type=order.order_type,
                parameters={
                    'order_id': order.id,
                    'type': order.order_type,
                    'broadcast_interval': order.broadcast_interval,
                    'playlist': [
                        {
                            'id': str(file.id),
                            'hash': file.hash,
                            'url': 'placeholder'
                        } for file in order.playlist.files.all()
                    ]
                }
            ) for client in clients
        ]
        count = len(list(task_list))
        try:
            Task.objects.bulk_create(task_list)
            successful_tasks += count
        except Exception as e:
            # TODO retry
            failed_tasks += count
            bg_logger.error(f'Не удалось переотправить {count} '
                            f'заказов: {task_list}.\nОшибка: {repr(e)}')

    result = f'Переотправленно заказов: {successful_tasks}. '
    if failed_tasks:
        result += f'Ошибки: {failed_tasks}'
    return result
