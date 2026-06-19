from django.utils import timezone

from celery import shared_task
from celery_singleton import Singleton

from api.constants import get_bg_task_type
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
    waiting_adorders = AdOrder.active.filter(status=0)
    waiting_bgorders = BgOrder.active.filter(status=0)
    ending_adorders = AdOrder.active.filter(status=1)
    ending_bgorders = BgOrder.active.filter(status=1)
    adorders_started = []
    bgorders_started = []
    adorders_ended = []
    bgorders_ended = []
    count = 0
    ON_AIR = 1
    COMPLETED = 2

    for order in waiting_adorders:
        order_start = order.broadcast_interval.lower
        if order_start <= timezone.now():
            order.status = ON_AIR
            adorders_started.append(order)
    count += len(adorders_started)
    AdOrder.active.bulk_update(adorders_started, fields=['status'])

    for order in ending_adorders:
        order_end = order.broadcast_interval.upper
        if order_end <= timezone.now():
            order.status = COMPLETED
            order.is_active = False
            adorders_ended.append(order)
    count += len(adorders_ended)
    AdOrder.active.bulk_update(adorders_ended, fields=['status', 'is_active'])

    for order in waiting_bgorders:
        order_start = order.broadcast_interval.lower
        if order_start <= timezone.now():
            order.status = ON_AIR
            bgorders_started.append(order)
    count += len(bgorders_started)
    BgOrder.active.bulk_update(bgorders_started, fields=['status'])

    for order in ending_bgorders:
        order_end = order.broadcast_interval.upper
        if order_end <= timezone.now():
            order.status = COMPLETED
            order.is_active = False
            bgorders_ended.append(order)
    count += len(bgorders_ended)
    BgOrder.active.bulk_update(bgorders_ended, fields=['status', 'is_active'])

    return f"Обновлено {count} статусов заказов."


@shared_task
def create_ad_order_task(orders_ids: list):
    """
    Отправка рекламного заказа.

    0. Фильтруем заказы по полученному списку.
    1. Проходим по получившемуся списку.
    2. Заполняем список репликаций, берём нужную инфу с заказа.
    3. Создаём все репликации одной операцией, фиксируем количество.
    """
    task_list = []
    AD = 4
    # 0
    orders = AdOrder.active.filter(pk__in=orders_ids)
    # 1
    for order in orders:
        # 2 - Форматируем время в нужный формат и добавляем ответственного
        broadcast_start = order.broadcast_interval.lower.strftime('%Y-%m-%d %H:%M:%S')
        broadcast_end = order.broadcast_interval.upper.strftime('%Y-%m-%d %H:%M:%S')
        
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=AD,
                parameters={
                    'order_id': str(order.id),
                    'order_parameters': order.parameters,
                    'broadcast_type': order.broadcast_type,
                    'responsible': order.owner.full_name,  # Добавляем ответственного
                    'broadcast_start': broadcast_start,
                    'broadcast_end': broadcast_end,
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
    result = f'Создано заказов: {len(task_list)}.'
    return result


@shared_task
def add_or_remove_files_ad_order_task(
    order_list: list[str],
    files: list[dict[str, str]] | list[str],
    action_type
):
    """
    Добавление/удаление файлов из активного заказа.

    В зависимости от действия (удаление/добавление) отдаётся список словарей,
    содержащий айдишки и хэши новых файлов, либо список с айдишками файлов,
    которые нужно убрать.

    0. Фильтруем заказы по айди.
    1. Собираем список репликаций, подставляем информацию из заказа,
        тип действия и список файлов.
    2. Создаём все репликации одним действием.
    3. В ответ отдаём количество созданных репликаций.
    """
    # 0
    orders = AdOrder.active.filter(id__in=order_list)
    UPDATE_AD = 14
    task_list = []
    # 1
    for order in orders:
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=UPDATE_AD,
                parameters={
                    'order_id': str(order.id),
                    'update_type': action_type,
                    'files': files,
                    'responsible': order.owner.full_name  # Добавляем ответственного
                }
            )
        )
    # 2
    Task.objects.bulk_create(task_list)
    # 3
    return f'Обновлено заказов: {len(task_list)}'


@shared_task
def update_ad_order_task(order_id: str):
    """
    Обновление плейлиста активного рекламного заказа.

    0. Находим объект заказа по айди.
    1. Создаём репликацию, параметры берём из заказа.
    2. В ответ отдаём айди обновлённого заказа.
    """
    # 0
    order = AdOrder.active.get(id=order_id)
    UPDATE_AD = 14
    # 1
    Task.objects.create(
        owner=order.owner,
        client=order.client,
        type=UPDATE_AD,
        parameters={
            'order_id': str(order.id),
            'playlist': {
                'id': str(order.playlist.id),
                'files': [
                    {
                        'id': str(file.id),
                        'hash': file.hash
                    } for file in order.playlist.files.all()
                ],
                'slides': order.slides if order.slides else None
            },
            'update_type': 'update_playlist',
            'responsible': order.owner.full_name  # Добавляем ответственного
        }
    )
    # 2
    return f'Обновлён заказ: {order_id}'


@shared_task
def cancel_ad_order_task(order_id: str):
    """
    Отмена рекламного заказа.

    0. Получаем объект заказа по его айди.
    1. Создаём репликацию отмены используя информацию из заказа.
    2. Меняем статус заказа на Отменён.
    3. В ответ отдаём айди отменённого заказа.
    """
    CANCEL = 3
    CANCEL_AD = 9
    # 0
    order = AdOrder.active.get(id=order_id)
    # 1
    Task.objects.create(
        owner=order.owner,
        client=order.client,
        type=CANCEL_AD,
        parameters={
            'order_id': order_id,
            'responsible': order.owner.full_name  # Добавляем ответственного
        }
    )
    # 2
    order.status = CANCEL
    order.is_active = False
    order.save(update_fields=['status', 'is_active'])
    # 3
    return f'Отменён заказ: {order_id}.'


@shared_task
def create_bg_order_task(orders_ids: list):
    """
    Отправка фонового заказа.

    0. Фильтруем заказы по полученному списку.
    1. Проходим по получившемуся списку.
    2. Заполняем список репликаций, берём нужную инфу с заказа.
    3. Создаём все репликации одной операцией, фиксируем количество.
    """
    # 0
    orders = BgOrder.active.filter(pk__in=orders_ids)
    task_list = []
    # 1
    for order in orders:
        # 2 - Форматируем время в нужный формат и добавляем ответственного
        broadcast_start = order.broadcast_interval.lower.strftime('%Y-%m-%d %H:%M:%S')
        # Для бессрочных заказов broadcast_end может быть None
        broadcast_end = None
        if order.broadcast_interval and order.broadcast_interval.upper:
            broadcast_end = order.broadcast_interval.upper.strftime('%Y-%m-%d %H:%M:%S')
        
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=order.order_type,
                parameters={
                    'order_id': str(order.id),
                    'order_type': order.order_type,
                    'responsible': order.owner.full_name,  # Добавляем ответственного
                    'is_permanent': order.is_permanent,  # Добавляем флаг бессрочности
                    'broadcast_start': broadcast_start,
                    'broadcast_end': broadcast_end,
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
def add_or_remove_files_bg_order_task(
    order_list: list[str],
    files: list[dict[str, str]] | list[str],
    action_type
):
    """
    Добавление/удаление файлов из активного заказа.

    В зависимости от действия (удаление/добавление) отдаётся список словарей,
    содержащий айдишки и хэши новых файлов, либо список с айдишками файлов,
    которые нужно убрать.

    0. Фильтруем заказы по айди.
    1. Подбираем тип репликации по типу первого заказа, т.к все заказы в списке
        будут одного типа.
    2. Собираем список репликаций, подставляем информацию из заказа,
        тип действия и список файлов.
    3. Создаём все репликации одним действием.
    4. В ответ отдаём количество созданных репликаций.
    """
    # 0
    orders = BgOrder.active.filter(id__in=order_list)
    # 1
    task_type = get_bg_task_type(orders[0].order_type, action='update')
    task_list = []
    # 2
    for order in orders:
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=task_type,
                parameters={
                    'order_id': str(order.id),
                    'update_type': action_type,
                    'files': files,
                    'responsible': order.owner.full_name  # Добавляем ответственного
                }
            )
        )
    # 3
    Task.objects.bulk_create(task_list)
    # 4
    return f'Обновлено заказов: {len(task_list)}'


@shared_task
def update_bg_order_task(order_id: str):
    """
    Обновление плейлиста активного фонового заказа.

    0. Находим заказ по айди.
    1. Подбираем тип репликации по типу заказа.
    2. Создаём репликацию, параметры берём из заказа.
    3. В ответ отдаём номер обновлённого заказа.
    """
    # 0
    order = BgOrder.active.get(id=order_id)
    # 1
    task_type = get_bg_task_type(order.order_type, action='update')
    # 2
    Task.objects.create(
        owner=order.owner,
        client=order.client,
        type=task_type,
        parameters={
            'order_id': str(order.id),
            'playlist': {
                'id': str(order.playlist.id),
                'files': [
                    {
                        'id': str(file.id),
                        'hash': file.hash
                    } for file in order.playlist.files.all()
                ]
            },
            'update_type': 'update_playlist',
            'responsible': order.owner.full_name  # Добавляем ответственного
        }
    )
    # 3
    return f'Обновлён заказ: {order_id}'


@shared_task
def cancel_bg_order_task(order_id: str):
    """
    Отмена фонового заказа.

    0. Получаем объект заказа по его айди.
    1. Получаем нужный тип репликации соответственно типу заказа.
    2. Создаём репликацию на отмену.
    3. Меняем статус заказа на Отменён.
    4. В ответ отдаём айди отменённого заказа.
    """
    CANCEL = 3
    # 0
    order = BgOrder.active.get(id=order_id)
    # 1
    task_type = get_bg_task_type(order.order_type, action='cancel')
    # 2
    Task.objects.create(
        owner=order.owner,
        client=order.client,
        type=task_type,
        parameters={
            'order_id': order_id,
            'responsible': order.owner.full_name  # Добавляем ответственного
        }
    )
    # 3
    order.status = CANCEL
    order.is_active = False
    order.save(update_fields=['status', 'is_active'])
    # 4
    result = f'Отменено заказов: {order_id}.'
    return result

# from django.utils import timezone

# from celery import shared_task
# from celery_singleton import Singleton

# from api.constants import get_bg_task_type
# from api.logger import setup_logger
# from orders.models import AdOrder, BgOrder
# from tasks.models import Task

# ad_logger = setup_logger('ad_orders', 'logs/ad_orders.log')
# bg_logger = setup_logger('bg_orders', 'logs/bg_orders.log')


# @shared_task(base=Singleton)
# def update_order_status():
#     """
#     Обновление статусов доступности номенклатур
#     и запись истории их изменения.
#     """
#     waiting_adorders = AdOrder.active.filter(status=0)
#     waiting_bgorders = BgOrder.active.filter(status=0)
#     ending_adorders = AdOrder.active.filter(status=1)
#     ending_bgorders = BgOrder.active.filter(status=1)
#     adorders_started = []
#     bgorders_started = []
#     adorders_ended = []
#     bgorders_ended = []
#     count = 0
#     ON_AIR = 1
#     COMPLETED = 2

#     for order in waiting_adorders:
#         order_start = order.broadcast_interval.lower
#         if order_start <= timezone.now():
#             order.status = ON_AIR
#             adorders_started.append(order)
#     count += len(adorders_started)
#     AdOrder.active.bulk_update(adorders_started, fields=['status'])

#     for order in ending_adorders:
#         order_end = order.broadcast_interval.upper
#         if order_end <= timezone.now():
#             order.status = COMPLETED
#             order.is_active = False
#             adorders_ended.append(order)
#     count += len(adorders_ended)
#     AdOrder.active.bulk_update(adorders_ended, fields=['status', 'is_active'])

#     for order in waiting_bgorders:
#         order_start = order.broadcast_interval.lower
#         if order_start <= timezone.now():
#             order.status = ON_AIR
#             bgorders_started.append(order)
#     count += len(bgorders_started)
#     BgOrder.active.bulk_update(bgorders_started, fields=['status'])

#     for order in ending_bgorders:
#         order_end = order.broadcast_interval.upper
#         if order_end <= timezone.now():
#             order.status = COMPLETED
#             order.is_active = False
#             bgorders_ended.append(order)
#     count += len(bgorders_ended)
#     BgOrder.active.bulk_update(bgorders_ended, fields=['status', 'is_active'])

#     return f"Обновлено {count} статусов заказов."


# @shared_task
# def create_ad_order_task(orders_ids: list):
#     """
#     Отправка рекламного заказа.

#     0. Фильтруем заказы по полученному списку.
#     1. Проходим по получившемуся списку.
#     2. Заполняем список репликаций, берём нужную инфу с заказа.
#     3. Создаём все репликации одной операцией, фиксируем количество.
#     """
#     task_list = []
#     AD = 4
#     # 0
#     orders = AdOrder.active.filter(pk__in=orders_ids)
#     # 1
#     for order in orders:
#         # 2
#         task_list.append(
#             Task(
#                 owner=order.owner,
#                 client=order.client,
#                 type=AD,
#                 parameters={
#                     'order_id': str(order.id),
#                     'order_parameters': order.parameters,
#                     'broadcast_type': order.broadcast_type,
#                     'broadcast_start': f'{order.broadcast_interval.lower}',
#                     'broadcast_end': f'{order.broadcast_interval.upper}',
#                     'playlist': {
#                         'id': str(order.playlist.id),
#                         'files': [
#                             {
#                                 'id': str(file.id),
#                                 'hash': file.hash
#                             } for file in order.playlist.files.all()
#                         ],
#                         'slides': order.slides if order.slides else None
#                     }
#                 }
#             )
#         )
#     # 3
#     Task.objects.bulk_create(task_list)
#     result = f'Создано заказов: {len(task_list)}.'
#     return result


# @shared_task
# def add_or_remove_files_ad_order_task(
#     order_list: list[str],
#     files: list[dict[str, str]] | list[str],
#     action_type
# ):
#     """
#     Добавление/удаление файлов из активного заказа.

#     В зависимости от действия (удаление/добавление) отдаётся список словарей,
#     содержащий айдишки и хэши новых файлов, либо список с айдишками файлов,
#     которые нужно убрать.

#     0. Фильтруем заказы по айди.
#     1. Собираем список репликаций, подставляем информацию из заказа,
#         тип действия и список файлов.
#     2. Создаём все репликации одним действием.
#     3. В ответ отдаём количество созданных репликаций.
#     """
#     # 0
#     orders = AdOrder.active.filter(id__in=order_list)
#     UPDATE_AD = 14
#     task_list = []
#     # 1
#     for order in orders:
#         task_list.append(
#             Task(
#                 owner=order.owner,
#                 client=order.client,
#                 type=UPDATE_AD,
#                 parameters={
#                     'order_id': str(order.id),
#                     'update_type': action_type,
#                     'files': files
#                 }
#             )
#         )
#     # 2
#     Task.objects.bulk_create(task_list)
#     # 3
#     return f'Обновлено заказов: {len(task_list)}'


# @shared_task
# def update_ad_order_task(order_id: str):
#     """
#     Обновление плейлиста активного рекламного заказа.

#     0. Находим объект заказа по айди.
#     1. Создаём репликацию, параметры берём из заказа.
#     2. В ответ отдаём айди обновлённого заказа.
#     """
#     # 0
#     order = AdOrder.active.get(id=order_id)
#     UPDATE_AD = 14
#     # 1
#     Task.objects.create(
#         owner=order.owner,
#         client=order.client,
#         type=UPDATE_AD,
#         parameters={
#             'order_id': str(order.id),
#             'playlist': {
#                         'id': str(order.playlist.id),
#                         'files': [
#                             {
#                                 'id': str(file.id),
#                                 'hash': file.hash
#                             } for file in order.playlist.files.all()
#                         ],
#                         'slides': order.slides if order.slides else None
#                     },
#             'update_type': 'update_playlist'
#         }
#     )
#     # 2
#     return f'Обновлён заказ: {order_id}'


# @shared_task
# def cancel_ad_order_task(order_id: str):
#     """
#     Отмена рекламного заказа.

#     0. Получаем объект заказа по его айди.
#     1. Создаём репликацию отмены используя информацию из заказа.
#     2. Меняем статус заказа на Отменён.
#     3. В ответ отдаём айди отменённого заказа.
#     """
#     CANCEL = 3
#     CANCEL_AD = 9
#     # 0
#     order = AdOrder.active.get(id=order_id)
#     # 1
#     Task.objects.create(
#         owner=order.owner,
#         client=order.client,
#         type=CANCEL_AD,
#         parameters={'order_id': order_id}
#     )
#     # 2
#     order.status = CANCEL
#     order.is_active = False
#     order.save(update_fields=['status', 'is_active'])
#     # 3
#     return f'Отменён заказ: {order_id}.'


# @shared_task
# def create_bg_order_task(orders_ids: list):
#     """
#     Отправка фонового заказа.

#     0. Фильтруем заказы по полученному списку.
#     1. Проходим по получившемуся списку.
#     2. Заполняем список репликаций, берём нужную инфу с заказа.
#     3. Создаём все репликации одной операцией, фиксируем количество.
#     """
#     # 0
#     orders = BgOrder.active.filter(pk__in=orders_ids)
#     task_list = []
#     # 1
#     for order in orders:
#         # 2
#         task_list.append(
#             Task(
#                 owner=order.owner,
#                 client=order.client,
#                 type=order.order_type,
#                 parameters={
#                     'order_id': str(order.id),
#                     'order_type': order.order_type,
#                     'broadcast_start': f'{order.broadcast_interval.lower}',
#                     'broadcast_end': f'{order.broadcast_interval.upper}',
#                     'playlist': {
#                         'id': str(order.playlist.id),
#                         # TODO протестировать разницу по времени выполнения
#                         # 100+ заказов в текущем исполнении и в таком:
#                         # 'files': list(
#                         #     map(lambda f: {'id': str(f.id), 'hash': f.hash},
#                         #         order.playlist.files.all())
#                         # )
#                         # сейчас каждый файл плейлиста индивидуально приводится к типу,
#                         # а во втором варианте файлы обрабатываются сразу скопом
#                         'files': [
#                             {
#                                 'id': str(file.id),
#                                 'hash': file.hash
#                             } for file in order.playlist.files.all()
#                         ]
#                     }
#                 }
#             )
#         )
#     # 3
#     Task.objects.bulk_create(task_list)
#     result = f'Создано заказов: {len(task_list)}.'
#     return result


# @shared_task
# def add_or_remove_files_bg_order_task(
#     order_list: list[str],
#     files: list[dict[str, str]] | list[str],
#     action_type
# ):
#     """
#     Добавление/удаление файлов из активного заказа.

#     В зависимости от действия (удаление/добавление) отдаётся список словарей,
#     содержащий айдишки и хэши новых файлов, либо список с айдишками файлов,
#     которые нужно убрать.

#     0. Фильтруем заказы по айди.
#     1. Подбираем тип репликации по типу первого заказа, т.к все заказы в списке
#         будут одного типа.
#     2. Собираем список репликаций, подставляем информацию из заказа,
#         тип действия и список файлов.
#     3. Создаём все репликации одним действием.
#     4. В ответ отдаём количество созданных репликаций.
#     """
#     # 0
#     orders = BgOrder.active.filter(id__in=order_list)
#     # 1
#     task_type = get_bg_task_type(orders[0].order_type, action='update')
#     task_list = []
#     # 2
#     for order in orders:
#         task_list.append(
#             Task(
#                 owner=order.owner,
#                 client=order.client,
#                 type=task_type,
#                 parameters={
#                     'order_id': str(order.id),
#                     'update_type': action_type,
#                     'files': files
#                 }
#             )
#         )
#     # 3
#     Task.objects.bulk_create(task_list)
#     # 4
#     return f'Обновлено заказов: {len(task_list)}'


# @shared_task
# def update_bg_order_task(order_id: str):
#     """
#     Обновление плейлиста активного фонового заказа.

#     0. Находим заказ по айди.
#     1. Подбираем тип репликации по типу заказа.
#     2. Создаём репликацию, параметры берём из заказа.
#     3. В ответ отдаём номер обновлённого заказа.
#     """
#     # 0
#     order = BgOrder.active.get(id=order_id)
#     # 1
#     task_type = get_bg_task_type(order.order_type, action='update')
#     # 2
#     Task.objects.create(
#         owner=order.owner,
#         client=order.client,
#         type=task_type,
#         parameters={
#             'order_id': str(order.id),
#             'playlist': {
#                 'id': str(order.playlist.id),
#                 'files': [
#                     {
#                         'id': str(file.id),
#                         'hash': file.hash
#                     } for file in order.playlist.files.all()
#                 ]
#             },
#             'update_type': 'update_playlist'
#         }
#     )
#     # 3
#     return f'Обновлён заказ: {order_id}'


# @shared_task
# def cancel_bg_order_task(order_id: str):
#     """
#     Отмена фонового заказа.

#     0. Получаем объект заказа по его айди.
#     1. Получаем нужный тип репликации соответственно типу заказа.
#     2. Создаём репликацию на отмену.
#     3. Меняем статус заказа на Отменён.
#     4. В ответ отдаём айди отменённого заказа.
#     """
#     CANCEL = 3
#     # 0
#     order = BgOrder.active.get(id=order_id)
#     # 1
#     task_type = get_bg_task_type(order.order_type, action='cancel')
#     # 2
#     Task.objects.create(
#         owner=order.owner,
#         client=order.client,
#         type=task_type,
#         parameters={'order_id': order_id}
#     )
#     # 3
#     order.status = CANCEL
#     order.is_active = False
#     order.save(update_fields=['status', 'is_active'])
#     # 4
#     result = f'Отменено заказов: {order_id}.'
#     return result
