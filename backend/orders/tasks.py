from datetime import datetime as dt
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
        if order_start <= dt.now():
            order.status = ON_AIR
            adorders_started.append(order)
    count += len(adorders_started)
    AdOrder.active.bulk_update(adorders_started, fields=['status'])

    for order in ending_adorders:
        order_end = order.broadcast_interval.upper
        if order_end <= dt.now():
            order.status = COMPLETED
            order.is_active = False
            adorders_ended.append(order)
    count += len(adorders_ended)
    AdOrder.active.bulk_update(adorders_ended, fields=['status', 'is_active'])

    for order in waiting_bgorders:
        order_start = order.broadcast_interval.lower
        if order_start <= dt.now():
            order.status = ON_AIR
            bgorders_started.append(order)
    count += len(bgorders_started)
    BgOrder.active.bulk_update(bgorders_started, fields=['status'])

    for order in ending_bgorders:
        order_end = order.broadcast_interval.upper
        if order_end <= dt.now():
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
    """
    task_list = []
    AD = 4
    orders = AdOrder.active.filter(pk__in=orders_ids)
    
    for order in orders:
        # Форматируем время без часового пояса
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
                    'responsible': order.owner.full_name,
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
    
    Task.objects.bulk_create(task_list)
    return f'Создано заказов: {len(task_list)}.'


@shared_task
def add_or_remove_files_ad_order_task(
    order_list: list[str],
    files: list[dict[str, str]] | list[str],
    action_type
):
    """
    Добавление/удаление файлов из активного заказа.
    """
    orders = AdOrder.active.filter(id__in=order_list)
    UPDATE_AD = 14
    task_list = []
    
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
                    'responsible': order.owner.full_name
                }
            )
        )
    
    Task.objects.bulk_create(task_list)
    return f'Обновлено заказов: {len(task_list)}'


@shared_task
def update_ad_order_task(order_id: str):
    """
    Обновление плейлиста активного рекламного заказа.
    """
    order = AdOrder.active.get(id=order_id)
    UPDATE_AD = 14
    
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
            'responsible': order.owner.full_name
        }
    )
    return f'Обновлён заказ: {order_id}'


@shared_task
def cancel_ad_order_task(order_id: str):
    """
    Отмена рекламного заказа.
    """
    CANCEL = 3
    CANCEL_AD = 9
    order = AdOrder.active.get(id=order_id)
    
    Task.objects.create(
        owner=order.owner,
        client=order.client,
        type=CANCEL_AD,
        parameters={
            'order_id': order_id,
            'responsible': order.owner.full_name
        }
    )
    
    order.status = CANCEL
    order.is_active = False
    order.save(update_fields=['status', 'is_active'])
    return f'Отменён заказ: {order_id}.'


@shared_task
def create_bg_order_task(orders_ids: list):
    """
    Отправка фонового заказа.
    """
    orders = BgOrder.active.filter(pk__in=orders_ids)
    task_list = []
    
    for order in orders:
        # Форматируем время без часового пояса
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
                    'responsible': order.owner.full_name,
                    'is_permanent': order.is_permanent,
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
    
    Task.objects.bulk_create(task_list)
    return f'Создано заказов: {len(task_list)}.'


@shared_task
def add_or_remove_files_bg_order_task(
    order_list: list[str],
    files: list[dict[str, str]] | list[str],
    action_type
):
    """
    Добавление/удаление файлов из активного заказа.
    """
    orders = BgOrder.active.filter(id__in=order_list)
    task_type = get_bg_task_type(orders[0].order_type, action='update')
    task_list = []
    
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
                    'responsible': order.owner.full_name
                }
            )
        )
    
    Task.objects.bulk_create(task_list)
    return f'Обновлено заказов: {len(task_list)}'


@shared_task
def update_bg_order_task(order_id: str):
    """
    Обновление плейлиста активного фонового заказа.
    """
    order = BgOrder.active.get(id=order_id)
    task_type = get_bg_task_type(order.order_type, action='update')
    
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
            'responsible': order.owner.full_name
        }
    )
    return f'Обновлён заказ: {order_id}'


@shared_task
def cancel_bg_order_task(order_id: str):
    """
    Отмена фонового заказа.
    """
    CANCEL = 3
    order = BgOrder.active.get(id=order_id)
    task_type = get_bg_task_type(order.order_type, action='cancel')
    
    Task.objects.create(
        owner=order.owner,
        client=order.client,
        type=task_type,
        parameters={
            'order_id': order_id,
            'responsible': order.owner.full_name
        }
    )
    
    order.status = CANCEL
    order.is_active = False
    order.save(update_fields=['status', 'is_active'])
    return f'Отменено заказов: {order_id}.'

# """
# Задачи Celery для управления заказами и репликациями.

# Этот модуль содержит все фоновые задачи для работы с заказами:
# - Создание репликаций для новых заказов
# - Обновление существующих заказов
# - Отмена заказов
# - Добавление/удаление файлов из заказов
# - Автоматическое обновление статусов заказов

# Все задачи используют Celery с синглтоном для предотвращения дублирования.
# """

# from django.utils import timezone

# from celery import shared_task
# from celery_singleton import Singleton

# from api.constants import get_bg_task_type
# from api.logger import setup_logger
# from orders.models import AdOrder, BgOrder
# from tasks.models import Task

# # Настройка логгеров для отслеживания операций с заказами
# ad_logger = setup_logger('ad_orders', 'logs/ad_orders.log')
# bg_logger = setup_logger('bg_orders', 'logs/bg_orders.log')


# @shared_task(base=Singleton)
# def update_order_status():
#     """
#     Автоматическое обновление статусов заказов.

#     Задача выполняется периодически (по расписанию Celery Beat) и проверяет
#     все активные заказы, обновляя их статусы в зависимости от текущего времени.

#     ЛОГИКА РАБОТЫ:
#     ───────────────────────────────────────────────────────────────────────────
#     1. Находит все заказы со статусом "Ожидает эфира" (status=0)
#        - Если время начала заказа (broadcast_interval.lower) <= текущее время
#          → переводит в статус "В эфире" (status=1)

#     2. Находит все заказы со статусом "В эфире" (status=1)
#        - Если время окончания заказа (broadcast_interval.upper) <= текущее время
#          → переводит в статус "Завершён" (status=2) и деактивирует заказ

#     3. Обновляет статусы массово (bulk_update) для оптимизации

#     ПРИМЕЧАНИЕ:
#     ───────────────────────────────────────────────────────────────────────────
#     - Использует timezone.now() для корректной работы с часовыми поясами
#     - Использует Singleton для предотвращения параллельного выполнения
#     - Работает как с рекламными, так и с фоновыми заказами

#     Returns:
#         str: Сообщение с количеством обновлённых заказов
#               Например: "Обновлено 5 статусов заказов."
#     """
#     # Получаем заказы, ожидающие начала эфира
#     waiting_adorders = AdOrder.active.filter(status=0)
#     waiting_bgorders = BgOrder.active.filter(status=0)
    
#     # Получаем заказы, находящиеся в эфире
#     ending_adorders = AdOrder.active.filter(status=1)
#     ending_bgorders = BgOrder.active.filter(status=1)
    
#     # Списки для массового обновления
#     adorders_started = []  # Рекламные заказы, которые нужно перевести в "В эфире"
#     bgorders_started = []  # Фоновые заказы, которые нужно перевести в "В эфире"
#     adorders_ended = []    # Рекламные заказы, которые нужно завершить
#     bgorders_ended = []    # Фоновые заказы, которые нужно завершить
    
#     count = 0
#     ON_AIR = 1      # Статус "В эфире"
#     COMPLETED = 2   # Статус "Завершён"

#     # ─── Обработка рекламных заказов, ожидающих начала ───
#     for order in waiting_adorders:
#         order_start = order.broadcast_interval.lower
#         if order_start <= timezone.now():
#             order.status = ON_AIR
#             adorders_started.append(order)
#     count += len(adorders_started)
#     AdOrder.active.bulk_update(adorders_started, fields=['status'])

#     # ─── Обработка рекламных заказов, завершающих эфир ───
#     for order in ending_adorders:
#         order_end = order.broadcast_interval.upper
#         if order_end <= timezone.now():
#             order.status = COMPLETED
#             order.is_active = False  # Деактивируем заказ
#             adorders_ended.append(order)
#     count += len(adorders_ended)
#     AdOrder.active.bulk_update(adorders_ended, fields=['status', 'is_active'])

#     # ─── Обработка фоновых заказов, ожидающих начала ───
#     for order in waiting_bgorders:
#         order_start = order.broadcast_interval.lower
#         if order_start <= timezone.now():
#             order.status = ON_AIR
#             bgorders_started.append(order)
#     count += len(bgorders_started)
#     BgOrder.active.bulk_update(bgorders_started, fields=['status'])

#     # ─── Обработка фоновых заказов, завершающих эфир ───
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
#     Создание репликаций для рекламных заказов.

#     Эта задача создаёт репликации (Task) для отправки на клиентские устройства.
#     Каждая репликация содержит всю необходимую информацию о заказе:
#     - Данные заказа (ID, параметры, тип вещания)
#     - Временные интервалы (в локальном времени)
#     - Плейлист с файлами и слайдами
#     - Информацию об ответственном сотруднике

#     АРГУМЕНТЫ:
#     ───────────────────────────────────────────────────────────────────────────
#     orders_ids (list): Список UUID заказов, для которых нужно создать репликации
#                        Например: ['550e8400-e29b-41d4-a716-446655440000', ...]

#     ПАРАМЕТРЫ РЕПЛИКАЦИИ (Task.parameters):
#     ───────────────────────────────────────────────────────────────────────────
#     {
#         'order_id': str,              # UUID заказа
#         'order_parameters': dict,     # Параметры заказа (weight, times_in_hour и т.д.)
#         'broadcast_type': int,        # Тип вещания (0-6)
#         'responsible': str,           # Полное имя создателя заказа
#         'broadcast_start': str,       # Начало вещания (формат: YYYY-MM-DD HH:MM:SS)
#         'broadcast_end': str,         # Окончание вещания (формат: YYYY-MM-DD HH:MM:SS)
#         'playlist': {
#             'id': str,                # UUID плейлиста
#             'files': [                # Список файлов в плейлисте
#                 {
#                     'id': str,        # UUID файла
#                     'hash': str       # Хеш файла для проверки целостности
#                 }
#             ],
#             'slides': dict | None     # Слайды для рекламы (если есть)
#         }
#     }

#     ТИПЫ РЕПЛИКАЦИЙ:
#     ───────────────────────────────────────────────────────────────────────────
#     type = 4 (AD) - рекламный заказ

#     Returns:
#         str: Сообщение с количеством созданных репликаций
#               Например: "Создано заказов: 3."
#     """
#     task_list = []
#     AD = 4  # Тип репликации для рекламного заказа
#     orders = AdOrder.active.filter(pk__in=orders_ids)
    
#     for order in orders:
#         # Конвертируем UTC в локальное время (Asia/Krasnoyarsk)
#         # Это необходимо, чтобы клиенты получали время в их часовом поясе
#         local_start = timezone.localtime(order.broadcast_interval.lower)
#         broadcast_start = local_start.strftime('%Y-%m-%d %H:%M:%S')
        
#         local_end = timezone.localtime(order.broadcast_interval.upper)
#         broadcast_end = local_end.strftime('%Y-%m-%d %H:%M:%S')
        
#         task_list.append(
#             Task(
#                 owner=order.owner,          # Кто создал репликацию
#                 client=order.client,        # На какую станцию отправляем
#                 type=AD,                    # Тип: рекламный заказ
#                 parameters={
#                     'order_id': str(order.id),
#                     'order_parameters': order.parameters,
#                     'broadcast_type': order.broadcast_type,
#                     'responsible': order.owner.full_name,  # Для отображения в админке
#                     'broadcast_start': broadcast_start,
#                     'broadcast_end': broadcast_end,
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
    
#     # Массовое создание репликаций для оптимизации производительности
#     Task.objects.bulk_create(task_list)
#     return f'Создано заказов: {len(task_list)}.'


# @shared_task
# def add_or_remove_files_ad_order_task(
#     order_list: list[str],
#     files: list[dict[str, str]] | list[str],
#     action_type
# ):
#     """
#     Добавление или удаление файлов из активного рекламного заказа.

#     Эта задача обновляет состав плейлиста в уже работающем заказе.
#     Используется для динамического изменения контента без пересоздания заказа.

#     АРГУМЕНТЫ:
#     ───────────────────────────────────────────────────────────────────────────
#     order_list (list[str]): Список UUID заказов для обновления
#     files (list): Список файлов для добавления/удаления
#         - При добавлении: [{'id': str, 'hash': str}, ...]
#         - При удалении: [str, str, ...] (только ID)
#     action_type (str): Тип операции
#         - 'add' - добавить файлы
#         - 'remove' - удалить файлы

#     ПАРАМЕТРЫ РЕПЛИКАЦИИ (Task.parameters):
#     ───────────────────────────────────────────────────────────────────────────
#     {
#         'order_id': str,          # UUID заказа
#         'update_type': str,       # 'add' или 'remove'
#         'files': list,            # Список файлов для операции
#         'responsible': str        # Полное имя инициатора изменений
#     }

#     ТИПЫ РЕПЛИКАЦИЙ:
#     ───────────────────────────────────────────────────────────────────────────
#     type = 14 (UPDATE_AD) - обновление рекламного заказа

#     Returns:
#         str: Сообщение с количеством обновлённых заказов
#     """
#     orders = AdOrder.active.filter(id__in=order_list)
#     UPDATE_AD = 14  # Тип репликации для обновления рекламного заказа
#     task_list = []
    
#     for order in orders:
#         task_list.append(
#             Task(
#                 owner=order.owner,
#                 client=order.client,
#                 type=UPDATE_AD,
#                 parameters={
#                     'order_id': str(order.id),
#                     'update_type': action_type,
#                     'files': files,
#                     'responsible': order.owner.full_name
#                 }
#             )
#         )
    
#     Task.objects.bulk_create(task_list)
#     return f'Обновлено заказов: {len(task_list)}'


# @shared_task
# def update_ad_order_task(order_id: str):
#     """
#     Полное обновление плейлиста активного рекламного заказа.

#     В отличие от add_or_remove_files_ad_order_task, эта задача полностью
#     заменяет плейлист заказа новым.

#     АРГУМЕНТЫ:
#     ───────────────────────────────────────────────────────────────────────────
#     order_id (str): UUID заказа для обновления

#     ПАРАМЕТРЫ РЕПЛИКАЦИИ (Task.parameters):
#     ───────────────────────────────────────────────────────────────────────────
#     {
#         'order_id': str,          # UUID заказа
#         'update_type': 'update_playlist',  # Тип обновления
#         'playlist': {             # Новый плейлист
#             'id': str,
#             'files': [{'id': str, 'hash': str}, ...],
#             'slides': dict | None
#         },
#         'responsible': str        # Полное имя инициатора
#     }

#     ТИПЫ РЕПЛИКАЦИЙ:
#     ───────────────────────────────────────────────────────────────────────────
#     type = 14 (UPDATE_AD) - обновление рекламного заказа

#     Returns:
#         str: Сообщение с ID обновлённого заказа
#     """
#     order = AdOrder.active.get(id=order_id)
#     UPDATE_AD = 14
    
#     Task.objects.create(
#         owner=order.owner,
#         client=order.client,
#         type=UPDATE_AD,
#         parameters={
#             'order_id': str(order.id),
#             'playlist': {
#                 'id': str(order.playlist.id),
#                 'files': [
#                     {
#                         'id': str(file.id),
#                         'hash': file.hash
#                     } for file in order.playlist.files.all()
#                 ],
#                 'slides': order.slides if order.slides else None
#             },
#             'update_type': 'update_playlist',
#             'responsible': order.owner.full_name
#         }
#     )
#     return f'Обновлён заказ: {order_id}'


# @shared_task
# def cancel_ad_order_task(order_id: str):
#     """
#     Отмена рекламного заказа.

#     Создаёт репликацию отмены и обновляет статус заказа в БД.
#     После отмены заказ становится неактивным и не будет использоваться.

#     АРГУМЕНТЫ:
#     ───────────────────────────────────────────────────────────────────────────
#     order_id (str): UUID заказа для отмены

#     ПОСЛЕДОВАТЕЛЬНОСТЬ ДЕЙСТВИЙ:
#     ───────────────────────────────────────────────────────────────────────────
#     1. Создаётся репликация отмены (type = CANCEL_AD)
#     2. Статус заказа меняется на "Отменён" (status = 3)
#     3. Заказ деактивируется (is_active = False)

#     ТИПЫ РЕПЛИКАЦИЙ:
#     ───────────────────────────────────────────────────────────────────────────
#     type = 9 (CANCEL_AD) - отмена рекламного заказа

#     Returns:
#         str: Сообщение с ID отменённого заказа
#     """
#     CANCEL = 3          # Статус "Отменён"
#     CANCEL_AD = 9       # Тип репликации для отмены рекламного заказа
#     order = AdOrder.active.get(id=order_id)
    
#     Task.objects.create(
#         owner=order.owner,
#         client=order.client,
#         type=CANCEL_AD,
#         parameters={
#             'order_id': order_id,
#             'responsible': order.owner.full_name
#         }
#     )
    
#     order.status = CANCEL
#     order.is_active = False
#     order.save(update_fields=['status', 'is_active'])
#     return f'Отменён заказ: {order_id}.'


# @shared_task
# def create_bg_order_task(orders_ids: list):
#     """
#     Создание репликаций для фоновых заказов.

#     Аналогична create_ad_order_task, но для фоновых заказов.
#     Поддерживает бессрочные заказы (is_permanent=True).

#     АРГУМЕНТЫ:
#     ───────────────────────────────────────────────────────────────────────────
#     orders_ids (list): Список UUID заказов для создания репликаций

#     ПАРАМЕТРЫ РЕПЛИКАЦИИ (Task.parameters):
#     ───────────────────────────────────────────────────────────────────────────
#     {
#         'order_id': str,              # UUID заказа
#         'order_type': int,            # Тип фонового контента (0-3)
#         'responsible': str,           # Полное имя создателя
#         'is_permanent': bool,         # Флаг бессрочности
#         'broadcast_start': str,       # Начало вещания
#         'broadcast_end': str | None,  # Окончание (None для бессрочных)
#         'playlist': {
#             'id': str,
#             'files': [{'id': str, 'hash': str}, ...]
#         }
#     }

#     ОСОБЕННОСТИ БЕССРОЧНЫХ ЗАКАЗОВ:
#     ───────────────────────────────────────────────────────────────────────────
#     - is_permanent = True
#     - broadcast_end = None (нет даты окончания)
#     - Используются как резервные плейлисты

#     ТИПЫ РЕПЛИКАЦИЙ:
#     ───────────────────────────────────────────────────────────────────────────
#     type = order.order_type (0-3):
#         0 - BGMUSIC (фоновая музыка)
#         1 - BGVIDEO (фоновое видео)
#         2 - BGIMAGE (фоновые картинки)
#         3 - TICKER (бегущая строка)

#     Returns:
#         str: Сообщение с количеством созданных репликаций
#     """
#     orders = BgOrder.active.filter(pk__in=orders_ids)
#     task_list = []
    
#     for order in orders:
#         # Конвертируем UTC в локальное время
#         local_start = timezone.localtime(order.broadcast_interval.lower)
#         broadcast_start = local_start.strftime('%Y-%m-%d %H:%M:%S')
        
#         # Для бессрочных заказов broadcast_end может быть None
#         broadcast_end = None
#         if order.broadcast_interval and order.broadcast_interval.upper:
#             local_end = timezone.localtime(order.broadcast_interval.upper)
#             broadcast_end = local_end.strftime('%Y-%m-%d %H:%M:%S')
        
#         task_list.append(
#             Task(
#                 owner=order.owner,
#                 client=order.client,
#                 type=order.order_type,  # Тип зависит от типа фонового контента
#                 parameters={
#                     'order_id': str(order.id),
#                     'order_type': order.order_type,
#                     'responsible': order.owner.full_name,
#                     'is_permanent': order.is_permanent,
#                     'broadcast_start': broadcast_start,
#                     'broadcast_end': broadcast_end,
#                     'playlist': {
#                         'id': str(order.playlist.id),
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
    
#     Task.objects.bulk_create(task_list)
#     return f'Создано заказов: {len(task_list)}.'


# @shared_task
# def add_or_remove_files_bg_order_task(
#     order_list: list[str],
#     files: list[dict[str, str]] | list[str],
#     action_type
# ):
#     """
#     Добавление или удаление файлов из активного фонового заказа.

#     Аналогична add_or_remove_files_ad_order_task, но для фоновых заказов.
#     Тип репликации определяется автоматически на основе типа заказа.

#     АРГУМЕНТЫ:
#     ───────────────────────────────────────────────────────────────────────────
#     order_list (list[str]): Список UUID заказов для обновления
#     files (list): Список файлов для добавления/удаления
#     action_type (str): 'add' или 'remove'

#     ОПРЕДЕЛЕНИЕ ТИПА РЕПЛИКАЦИИ:
#     ───────────────────────────────────────────────────────────────────────────
#     Используется get_bg_task_type(order.order_type, action='update')
#     для получения соответствующего типа обновления:
#         - 10 (UPDATE_BGMUSIC)
#         - 11 (UPDATE_BGVIDEO)
#         - 12 (UPDATE_BGIMAGE)
#         - 13 (UPDATE_TICKER)

#     Returns:
#         str: Сообщение с количеством обновлённых заказов
#     """
#     orders = BgOrder.active.filter(id__in=order_list)
#     # Определяем тип репликации на основе типа первого заказа
#     # (все заказы в списке должны быть одного типа)
#     task_type = get_bg_task_type(orders[0].order_type, action='update')
#     task_list = []
    
#     for order in orders:
#         task_list.append(
#             Task(
#                 owner=order.owner,
#                 client=order.client,
#                 type=task_type,
#                 parameters={
#                     'order_id': str(order.id),
#                     'update_type': action_type,
#                     'files': files,
#                     'responsible': order.owner.full_name
#                 }
#             )
#         )
    
#     Task.objects.bulk_create(task_list)
#     return f'Обновлено заказов: {len(task_list)}'


# @shared_task
# def update_bg_order_task(order_id: str):
#     """
#     Полное обновление плейлиста активного фонового заказа.

#     Аналогична update_ad_order_task, но для фоновых заказов.

#     АРГУМЕНТЫ:
#     ───────────────────────────────────────────────────────────────────────────
#     order_id (str): UUID заказа для обновления

#     Returns:
#         str: Сообщение с ID обновлённого заказа
#     """
#     order = BgOrder.active.get(id=order_id)
#     task_type = get_bg_task_type(order.order_type, action='update')
    
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
#             'update_type': 'update_playlist',
#             'responsible': order.owner.full_name
#         }
#     )
#     return f'Обновлён заказ: {order_id}'


# @shared_task
# def cancel_bg_order_task(order_id: str):
#     """
#     Отмена фонового заказа.

#     Аналогична cancel_ad_order_task, но для фоновых заказов.

#     АРГУМЕНТЫ:
#     ───────────────────────────────────────────────────────────────────────────
#     order_id (str): UUID заказа для отмены

#     ТИПЫ РЕПЛИКАЦИЙ:
#     ───────────────────────────────────────────────────────────────────────────
#     Тип определяется через get_bg_task_type(order.order_type, action='cancel'):
#         - 5 (CANCEL_BGMUSIC)
#         - 6 (CANCEL_BGVIDEO)
#         - 7 (CANCEL_BGIMAGE)
#         - 8 (CANCEL_TICKER)

#     Returns:
#         str: Сообщение с ID отменённого заказа
#     """
#     CANCEL = 3  # Статус "Отменён"
#     order = BgOrder.active.get(id=order_id)
#     task_type = get_bg_task_type(order.order_type, action='cancel')
    
#     Task.objects.create(
#         owner=order.owner,
#         client=order.client,
#         type=task_type,
#         parameters={
#             'order_id': order_id,
#             'responsible': order.owner.full_name
#         }
#     )
    
#     order.status = CANCEL
#     order.is_active = False
#     order.save(update_fields=['status', 'is_active'])
#     return f'Отменено заказов: {order_id}.'

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
