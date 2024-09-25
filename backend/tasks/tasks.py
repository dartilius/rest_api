from celery import shared_task

from orders.models import AdOrder, BgOrder
from tasks.models import Task


@shared_task
def create_ad_order_task(orders_ids: list):
    """Создание репликации AD."""
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
        except Exception:
            del_order = AdOrder.objects.get(pk=order.id)
            del_order.delete()
            failed_tasks += count

    return f'Создано заказов: {successful_tasks}. Ошибки: {failed_tasks}'


@shared_task
def update_ad_order_task(orders_ids: list, updated_data: dict):
    pass
    # orders = AdOrder.objects.filter(pk__in=orders_ids)
    # successful_tasks = 0
    # failed_tasks = {'orders': [],
    #                 'count': 0}
    # for order in orders:
    #     clients = order.group.clients.all()
    #     task_list = [
    #         Task(
    #             owner=order.owner,
    #             client=client,
    #             type=14,
    #             parameters={
    #                 'order_id': order.id,
    #                 'updated_data': updated_data
    #             }
    #         ) for client in clients
    #     ]
    #     count = len(list(task_list))
    #     try:
    #         Task.objects.bulk_create(task_list)
    #         successful_tasks += count
    #     except Exception:
    #         failed_tasks['orders'].append(order)
    #         failed_tasks['count'] += count
    #
    # return (f'Создано заказов: {successful_tasks}. '
    #         f'Не удалось обновить данные для {failed_tasks["count"]} '
    #         f'заказов: {failed_tasks["orders"]}',
    #         failed_tasks['orders'])


@shared_task
def cancel_ad_order_task(orders_ids: list):
    """Отмена AD заказа."""
    orders = AdOrder.objects.filter(pk__in=orders_ids)
    for order in orders:
        clients = order.group.clients.all()
        task_list = (
            Task(
                owner=order.owner,
                client=client,
                type=9,
                parameters={'order_id': order.id}
            ) for client in clients
        )
        Task.objects.bulk_create(task_list)
        order.status = 3
        order.save()

    return f'Рекламных заказов отменено: {len(orders)}'


@shared_task
def create_bg_order_task(orders_ids: list):
    """Создание репликации BG."""
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
        except Exception:
            del_order = AdOrder.objects.get(pk=order.id)
            del_order.delete()
            failed_tasks += count

    return f'Создано заказов: {successful_tasks}. Ошибки: {failed_tasks}'


@shared_task
def update_bg_order_task(order_id: int, updated_data: dict):
    pass
    # """Обновление репликации BG."""
    # order = BgOrder.objects.get(pk=order_id)
    # successful_tasks = 0
    # failed_tasks = {'orders': [],
    #                 'count': 0}
    # clients = order.group.clients.all()
    # # order_type -> update_{order_type}
    # match order.order_type:
    #     case 0: task_type = 10
    #     case 1: task_type = 11
    #     case 2: task_type = 12
    #     case 3: task_type = 13
    # task_list = [
    #     Task(
    #         owner=order.owner,
    #         client=client,
    #         type=task_type,
    #         parameters={
    #             'order_id': order_id,
    #             'updated_data': updated_data
    #         }
    #     ) for client in clients
    # ]
    # count = len(list(task_list))
    # try:
    #     Task.objects.bulk_create(task_list)
    #     successful_tasks += count
    # except Exception:
    #     failed_tasks['orders'].append(order)
    #     failed_tasks['count'] += count
    #
    # return (f'Создано заказов: {successful_tasks}. '
    #         f'Не удалось обновить данные для {failed_tasks["count"]} '
    #         f'заказов: {failed_tasks["orders"]}')


@shared_task
def cancel_bg_order_task(orders_ids: list):
    orders = BgOrder.objects.filter(pk__in=orders_ids)
    try:
        for order in orders:
            clients = order.group.clients.all()
            # order_type -> cancel_{order_type}
            match order.order_type:
                case 0: task_type = 5
                case 1: task_type = 6
                case 2: task_type = 7
                case 3: task_type = 8
            task_list = (
                Task(
                    owner=order.owner,
                    client=client,
                    type=task_type,
                    parameters={'order_id': order.id}
                ) for client in clients
            )
            Task.objects.bulk_create(task_list)
            order.status = 3
            order.save()

        return f'Фоновых заказов отменено: {len(orders)}'

    except Exception:
        return False
