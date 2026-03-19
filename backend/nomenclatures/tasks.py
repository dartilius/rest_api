from itertools import chain

from celery import shared_task
from celery_singleton import Singleton
from datetime import datetime, timedelta
from django.contrib.postgres.search import SearchVector
from django.db.models import OuterRef, Subquery, Value
from django.db.models.functions import Coalesce, Concat
from nomenclatures.models import NomenclatureAvailability, StatusHistory, Nomenclature, NomenclatureTenant
from orders.models import AdOrder, BgOrder
from tasks.models import Task
from users.models import CustomUser
from django.contrib.postgres.aggregates import StringAgg
@shared_task
def update_all_search_vectors(batch_size=500):
    """
    Массовое обновление поля search_vector для всех номенклатур
    с учётом M2M tenants через промежуточную таблицу.
    """
    qs = Nomenclature.objects.all()
    total = qs.count()

    for start in range(0, total, batch_size):
        batch = list(qs[start:start+batch_size])

        tenants_subquery = NomenclatureTenant.objects.filter(
            nomenclature=OuterRef('pk')
        ).annotate(
            tenant_full=Concat(
                'tenant__first_name', Value(' '),
                'tenant__last_name', Value(' '),
                'tenant__additional_name', Value(' '),
                'tenant__keyword', Value(' '),
                Coalesce('floor', Value(''))
            )
        ).values('tenant_full')

        tenants_agg = Subquery(
            tenants_subquery.annotate(
                all_text=StringAgg('tenant_full', delimiter=' ')
            ).values('all_text')
        )

        # Обновляем search_vector для каждой номенклатуры в батче
        for n in batch:
            n.search_vector = (
                SearchVector('name', weight='A') +
                SearchVector('contentType', weight='C') +
                SearchVector('typeOfPlace__name', weight='B') +
                SearchVector('version', weight='B') +
                SearchVector('code1c', weight='A') +
                SearchVector('brand__name', weight='A') +
                SearchVector('legalEntity__first_name', weight='A') +
                SearchVector('legalEntity__last_name', weight='B') +
                SearchVector('legalEntity__keyword', weight='A') +
                SearchVector('legalEntity__additional_name', weight='C') +
                SearchVector('responsible_radio__first_name', weight='A') +
                SearchVector('responsible_ad__first_name', weight='A') +
                SearchVector('responsible_technic__first_name', weight='A') +
                SearchVector('responsible_technic_on_address__last_name', weight='B') +
                SearchVector('responsible_radio__last_name', weight='B') +
                SearchVector('responsible_ad__last_name', weight='B') +
                SearchVector('responsible_technic__last_name', weight='B') +
                SearchVector('responsible_technic_on_address__last_name', weight='B') +
                SearchVector(Coalesce(tenants_agg, Value('')), weight='B')  # M2M tenants

            )
        Nomenclature.objects.bulk_update(batch, ['search_vector'])

def get_owner(owner_id):
    return CustomUser.objects.get(pk=owner_id)


def get_nomenclature(nomenclature_id):
    return Nomenclature.objects.get(pk=nomenclature_id)


@shared_task(base=Singleton)
def update_nomenclature_status():
    """
    Обновление статусов доступности номенклатур
    и запись истории их изменения.
    """
    statuses = NomenclatureAvailability.objects.all()
    statuses_to_update = []
    status_histories_to_create = []
    ONLINE = 0
    OFFLINE_5_MIN = 1
    OFFLINE_1_HOUR = 2

    for status in statuses:
        now_time = datetime.now()
        new_status = ONLINE
        current_status = status.status
        last_answer = status.last_answer_date
        if current_status == ONLINE:
            if now_time - last_answer > timedelta(hours=1):
                new_status = OFFLINE_1_HOUR
            elif now_time - last_answer > timedelta(minutes=5):
                new_status = OFFLINE_5_MIN
            if new_status != current_status:
                status.status = new_status
                statuses_to_update.append(status)
                status_histories_to_create.append(
                    StatusHistory(
                        status=new_status,
                        client=status.client
                    )
                )

        if current_status == OFFLINE_5_MIN:
            new_status = OFFLINE_5_MIN
            if now_time - last_answer > timedelta(hours=1):
                new_status = OFFLINE_1_HOUR
            elif now_time - last_answer < timedelta(minutes=5):
                new_status = ONLINE
            if new_status != current_status:
                status.status = new_status
                statuses_to_update.append(status)
                status_histories_to_create.append(
                    StatusHistory(
                        status=new_status,
                        client=status.client
                    )
                )

        if current_status == OFFLINE_1_HOUR:
            if now_time - last_answer < timedelta(minutes=5):
                status.status = ONLINE
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
def resend_orders_task(nomenclature_id: int):
    """
    Переотправка заказов.

    1. Собираем список всех актуальных заказов, которые есть у номенклатуры.
    2. Проходим по списку заказов. Собираем параметры репликации,
        в зависимости от типа заказа.
    3. Формируем список репликаций для создания.
    4. Создаём все репликации одной операцией, фиксируем их количество.
    """
    task_list = []
    AD = 4
    # 1
    orders = chain(
        AdOrder.objects.filter(client=nomenclature_id, status__in=[0, 1]),
        BgOrder.objects.filter(client=nomenclature_id, status__in=[0, 1])
    )
    # 2
    for order in orders:
        parameters = {
            'order_id': str(order.id),
            'broadcast_start': f'{order.broadcast_interval.lower}',
            'broadcast_end': f'{order.broadcast_interval.upper}',
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
        if isinstance(order, AdOrder):
            parameters.update({
                'order_parameters': order.parameters,
                'broadcast_type': order.broadcast_type,
            })
            parameters['playlist']['slides'] = (
                order.slides if order.slides else None
            )
            task_type = AD
        else:
            parameters.update({'order_type': order.order_type})
            task_type = order.order_type
        # 3
        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=task_type,
                parameters=parameters
            )
        )
    # 4
    Task.objects.bulk_create(task_list)
    result = f'Переотправленно заказов: {len(task_list)}.'
    return result


@shared_task
def reboot_task(nomenclature_id: str, owner_id: str):
    nomenclature = get_nomenclature(nomenclature_id)
    owner = get_owner(owner_id)
    Task.objects.create(
        owner=owner,
        client=nomenclature,
        type=15
    )
    return f'Перезагрузка отправлена на {nomenclature.name}'


@shared_task
def update_task(nomenclature_id: str, owner_id: str):
    nomenclature = get_nomenclature(nomenclature_id)
    owner = get_owner(owner_id)
    Task.objects.create(
        owner=owner,
        client=nomenclature,
        type=16
    )
    return f'Обновление отправлено на {nomenclature.name}'


@shared_task
def custom_task(nomenclature_id: str, parameters: str, owner_id: str):
    nomenclature = get_nomenclature(nomenclature_id)
    owner = get_owner(owner_id)
    Task.objects.create(
        owner=owner,
        client=nomenclature,
        type=17,
        parameters=parameters
    )
    return f'SH команда отправлена на {nomenclature.name}'


@shared_task
def settings_task(nomenclature_id: str, owner_id: str):
    nomenclature = get_nomenclature(nomenclature_id)
    owner = get_owner(owner_id)
    Task.objects.create(
        owner=owner,
        client=nomenclature,
        type=18,
        parameters=nomenclature.settings
    )
    return f'Настройки вещания отправлены на {nomenclature.name}'
