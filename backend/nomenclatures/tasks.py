from itertools import chain

from celery import shared_task
from celery_singleton import Singleton
from nomenclatures.models import NomenclatureAvailability, StatusHistory, Nomenclature
from orders.models import AdOrder, BgOrder
from tasks.models import Task
from users.models import CustomUser
from datetime import timedelta
from django.utils import timezone

@shared_task(base=Singleton)
def update_opensearch_for_instance(instance_id):
    """Обновление документа в OpenSearch для конкретной номенклатуры."""
    try:
        from nomenclatures.documents import NomenclatureDocument
        from nomenclatures.models import Nomenclature

        # 🔴 Добавляем оптимизацию запроса
        nomenclature = (
            Nomenclature.objects
            .select_related(
                'brand',
                'legalEntity',
                'typeOfPlace',
                'responsible_radio',
                'responsible_ad',
                'responsible_technic',
                'responsible_technic_on_address',
                'responsible_placement_marketing',
            )
            .prefetch_related(
                'nomenclature_tenants__tenant',
                'nomenclature_tenants__brand',
            )
            .get(id=instance_id)
        )

        # Индексация документа в OpenSearch
        NomenclatureDocument().index(nomenclature)

        print(f"✅ OpenSearch обновлён для номенклатуры {instance_id}")
    except Nomenclature.DoesNotExist:
        print(f"❌ Номенклатура {instance_id} не найдена")
    except Exception as e:
        print(f"❌ Ошибка OpenSearch для {instance_id}: {e}")


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
        now_time = timezone.now()
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
