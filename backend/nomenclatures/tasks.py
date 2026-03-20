from itertools import chain
import logging
import time

from celery import shared_task, group
from celery_singleton import Singleton
from datetime import datetime, timedelta
from django.db import transaction, connection
from django.db.models import Q, F
from django.utils import timezone

from nomenclatures.models import NomenclatureAvailability, StatusHistory, Nomenclature, NomenclatureTenant
from orders.models import AdOrder, BgOrder
from tasks.models import Task
from users.models import CustomUser

logger = logging.getLogger(__name__)


# ================ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ================

def get_owner(owner_id):
    return CustomUser.objects.get(pk=owner_id)


def get_nomenclature(nomenclature_id):
    return Nomenclature.objects.get(pk=nomenclature_id)


# ================ ИНКРЕМЕНТАЛЬНОЕ ОБНОВЛЕНИЕ ПОИСКОВЫХ ВЕКТОРОВ ================

@shared_task(base=Singleton, soft_time_limit=300, time_limit=600)
def schedule_incremental_update(hours=24, batch_size=100):
    """
    Планирует обновление только измененных номенклатур за последние N часов
    """
    from nomenclatures.models import Nomenclature, NomenclatureTenant

    cutoff = timezone.now() - timedelta(hours=hours)

    # Находим номенклатуры, которые изменились
    changed_nomenclatures = Nomenclature.objects.filter(
        Q(updated_at__gte=cutoff) |
        Q(search_vector_updated_at__isnull=True) |  # никогда не обновлялись
        Q(search_vector_updated_at__lt=F('updated_at'))  # устаревший вектор
    ).values_list('id', flat=True)

    # Также учитываем номенклатуры, у которых изменились арендаторы
    nomenclatures_with_tenant_changes = NomenclatureTenant.objects.filter(
        updated_at__gte=cutoff
    ).values_list('nomenclature_id', flat=True).distinct()

    # Объединяем и убираем дубликаты
    all_changed_ids = set(chain(changed_nomenclatures, nomenclatures_with_tenant_changes))
    total = len(all_changed_ids)

    if total == 0:
        logger.info("Нет номенклатур для инкрементального обновления")
        return "Нет номенклатур для обновления"

    logger.info(f"Найдено {total} номенклатур для инкрементального обновления")

    # Разбиваем на батчи и создаем задачи
    all_ids_list = list(all_changed_ids)
    tasks = []

    for i in range(0, total, batch_size):
        batch_ids = all_ids_list[i:i + batch_size]
        tasks.append(update_search_vectors_batch.s(batch_ids))

    # Запускаем группу задач
    if tasks:
        group(tasks).apply_async()

    return f"Запланировано обновление {total} номенклатур в {len(tasks)} батчах"


@shared_task(soft_time_limit=180, time_limit=300)  # 3-5 минут на батч
def update_search_vectors_batch(nomenclature_ids):
    """
    Обновляет search_vector для батча номенклатур
    """
    if not nomenclature_ids:
        return "Пустой батч"

    logger.info(f"Обновление батча из {len(nomenclature_ids)} номенклатур")

    # Предзагружаем всех арендаторов для этого батча
    tenants_by_nomenclature = {}

    # Используем select_related и values для оптимизации
    tenant_data = NomenclatureTenant.objects.filter(
        nomenclature_id__in=nomenclature_ids
    ).select_related('tenant').values(
        'nomenclature_id',
        'tenant__first_name',
        'tenant__last_name',
        'tenant__additional_name',
        'tenant__keyword',
        'floor'
    )

    # Агрегируем данные арендаторов
    for td in tenant_data:
        n_id = td['nomenclature_id']
        if n_id not in tenants_by_nomenclature:
            tenants_by_nomenclature[n_id] = []

        tenant_text = ' '.join(filter(None, [
            td['tenant__first_name'] or '',
            td['tenant__last_name'] or '',
            td['tenant__additional_name'] or '',
            td['tenant__keyword'] or '',
            str(td['floor']) if td['floor'] else ''
        ]))
        tenants_by_nomenclature[n_id].append(tenant_text)

    # Обновляем номенклатуры
    updated = 0
    errors = 0

    with transaction.atomic():
        nomenclatures = Nomenclature.objects.filter(
            id__in=nomenclature_ids
        ).select_related(
            'typeOfPlace', 'brand', 'legalEntity',
            'responsible_radio', 'responsible_ad',
            'responsible_technic', 'responsible_technic_on_address'
        )

        for nomenclature in nomenclatures:
            try:
                tenants_text = ' '.join(tenants_by_nomenclature.get(nomenclature.id, []))

                # Обновляем search_vector
                from django.contrib.postgres.search import SearchVector
                from django.db.models import Value

                nomenclature.search_vector = (
                        SearchVector(Value(nomenclature.name or ''), weight='A') +
                        SearchVector(Value(nomenclature.contentType or ''), weight='C') +
                        SearchVector(Value(nomenclature.typeOfPlace.name if nomenclature.typeOfPlace else ''),
                                     weight='B') +
                        SearchVector(Value(nomenclature.version or ''), weight='B') +
                        SearchVector(Value(nomenclature.code1c or ''), weight='A') +
                        SearchVector(Value(nomenclature.brand.name if nomenclature.brand else ''), weight='A') +
                        SearchVector(Value(nomenclature.legalEntity.first_name if nomenclature.legalEntity else ''),
                                     weight='A') +
                        SearchVector(Value(nomenclature.legalEntity.last_name if nomenclature.legalEntity else ''),
                                     weight='B') +
                        SearchVector(Value(nomenclature.legalEntity.keyword if nomenclature.legalEntity else ''),
                                     weight='A') +
                        SearchVector(
                            Value(nomenclature.legalEntity.additional_name if nomenclature.legalEntity else ''),
                            weight='C') +
                        SearchVector(
                            Value(nomenclature.responsible_radio.first_name if nomenclature.responsible_radio else ''),
                            weight='A') +
                        SearchVector(
                            Value(nomenclature.responsible_ad.first_name if nomenclature.responsible_ad else ''),
                            weight='A') +
                        SearchVector(Value(
                            nomenclature.responsible_technic.first_name if nomenclature.responsible_technic else ''),
                                     weight='A') +
                        SearchVector(Value(
                            nomenclature.responsible_technic_on_address.last_name if nomenclature.responsible_technic_on_address else ''),
                                     weight='B') +
                        SearchVector(
                            Value(nomenclature.responsible_radio.last_name if nomenclature.responsible_radio else ''),
                            weight='B') +
                        SearchVector(
                            Value(nomenclature.responsible_ad.last_name if nomenclature.responsible_ad else ''),
                            weight='B') +
                        SearchVector(Value(
                            nomenclature.responsible_technic.last_name if nomenclature.responsible_technic else ''),
                                     weight='B') +
                        SearchVector(Value(tenants_text), weight='B')
                )

                nomenclature.search_vector_updated_at = timezone.now()
                nomenclature.save(update_fields=['search_vector', 'search_vector_updated_at'])
                updated += 1

            except Exception as e:
                errors += 1
                logger.error(f"Ошибка при обновлении номенклатуры {nomenclature.id}: {e}")

    logger.info(f"Батч обновлен: {updated} успешно, {errors} ошибок")
    return f"Батч обновлен: {updated}/{len(nomenclature_ids)}"


# ================ ПОЛНОЕ ОБНОВЛЕНИЕ (ЕЖЕНЕДЕЛЬНОЕ) ================

@shared_task(base=Singleton, soft_time_limit=7200, time_limit=10800)  # 2-3 часа
def full_update_all_search_vectors(batch_size=200):
    """
    Полное обновление всех search_vector (раз в неделю)
    """
    total = Nomenclature.objects.count()
    logger.info(f"НАЧАЛО ПОЛНОГО ОБНОВЛЕНИЯ: {total} номенклатур")

    all_ids = list(Nomenclature.objects.values_list('id', flat=True))
    tasks = []

    # Создаем задачи для всех батчей
    for i in range(0, total, batch_size):
        batch_ids = all_ids[i:i + batch_size]
        tasks.append(full_update_batch.s(batch_ids, i // batch_size + 1, (total + batch_size - 1) // batch_size))

    # Запускаем все задачи
    if tasks:
        group(tasks).apply_async()
        logger.info(f"Запущено {len(tasks)} задач полного обновления")
        return f"Запущено полное обновление {total} номенклатур в {len(tasks)} батчах"

    return "Нет номенклатур для обновления"


@shared_task(soft_time_limit=600, time_limit=900)  # 10-15 минут на батч
def full_update_batch(nomenclature_ids, batch_num, total_batches):
    """
    Полное обновление батча номенклатур (использует оптимизированный SQL)
    """
    start_time = time.time()
    logger.info(f"Батч {batch_num}/{total_batches}: обновление {len(nomenclature_ids)} номенклатур")

    try:
        with connection.cursor() as cursor:
            # Создаем временную таблицу с агрегированными данными арендаторов
            cursor.execute("""
                CREATE TEMP TABLE temp_tenant_agg_{batch} AS
                SELECT 
                    nt.nomenclature_id,
                    string_agg(
                        COALESCE(u.first_name, '') || ' ' ||
                        COALESCE(u.last_name, '') || ' ' ||
                        COALESCE(u.additional_name, '') || ' ' ||
                        COALESCE(u.keyword, '') || ' ' ||
                        COALESCE(nt.floor::text, ''),
                        ' '
                    ) as tenants_text
                FROM nomenclatures_nomenclaturetenant nt
                JOIN users_customuser u ON u.id = nt.tenant_id
                WHERE nt.nomenclature_id = ANY(%s)
                GROUP BY nt.nomenclature_id
            """.format(batch=batch_num), [nomenclature_ids])

            # Массовое обновление search_vector
            cursor.execute("""
                UPDATE nomenclatures_nomenclature n
                SET search_vector = 
                    setweight(to_tsvector('russian', COALESCE(n.name, '')), 'A') ||
                    setweight(to_tsvector('russian', COALESCE(n."contentType", '')), 'C') ||
                    setweight(to_tsvector('russian', COALESCE(tp.name, '')), 'B') ||
                    setweight(to_tsvector('russian', COALESCE(n.version, '')), 'B') ||
                    setweight(to_tsvector('russian', COALESCE(n.code1c, '')), 'A') ||
                    setweight(to_tsvector('russian', COALESCE(b.name, '')), 'A') ||
                    setweight(to_tsvector('russian', 
                        COALESCE(le.first_name, '') || ' ' ||
                        COALESCE(le.last_name, '') || ' ' ||
                        COALESCE(le.keyword, '') || ' ' ||
                        COALESCE(le.additional_name, '')
                    ), 'A') ||
                    setweight(to_tsvector('russian', 
                        COALESCE(rr.first_name, '') || ' ' || COALESCE(rr.last_name, '')
                    ), 'A') ||
                    setweight(to_tsvector('russian', 
                        COALESCE(ra.first_name, '') || ' ' || COALESCE(ra.last_name, '')
                    ), 'A') ||
                    setweight(to_tsvector('russian', 
                        COALESCE(rt.first_name, '') || ' ' || COALESCE(rt.last_name, '')
                    ), 'A') ||
                    setweight(to_tsvector('russian', 
                        COALESCE(rto.first_name, '') || ' ' || COALESCE(rto.last_name, '')
                    ), 'B') ||
                    setweight(to_tsvector('russian', COALESCE(ta.tenants_text, '')), 'B'),

                    search_vector_updated_at = NOW()

                FROM nomenclatures_nomenclature n2
                LEFT JOIN nomenclatures_typeofplace tp ON tp.id = n2."typeOfPlace_id"
                LEFT JOIN nomenclatures_brand b ON b.id = n2."brand_id"
                LEFT JOIN users_customuser le ON le.id = n2."legalEntity_id"
                LEFT JOIN users_customuser rr ON rr.id = n2."responsible_radio_id"
                LEFT JOIN users_customuser ra ON ra.id = n2."responsible_ad_id"
                LEFT JOIN users_customuser rt ON rt.id = n2."responsible_technic_id"
                LEFT JOIN users_customuser rto ON rto.id = n2."responsible_technic_on_address_id"
                LEFT JOIN temp_tenant_agg_{batch} ta ON ta.nomenclature_id = n2.id
                WHERE n.id = n2.id AND n2.id = ANY(%s)
            """.format(batch=batch_num), [nomenclature_ids])

            updated = cursor.rowcount

            # Очищаем временную таблицу
            cursor.execute("DROP TABLE IF EXISTS temp_tenant_agg_{batch}".format(batch=batch_num))

        elapsed = time.time() - start_time
        logger.info(f"Батч {batch_num}/{total_batches} завершен: обновлено {updated} номенклатур за {elapsed:.2f}с")

        return f"Батч {batch_num}: обновлено {updated} номенклатур"

    except Exception as e:
        logger.error(f"Ошибка в батче {batch_num}: {e}")
        # Пробуем обновить по одной в случае ошибки
        return fallback_batch_update(nomenclature_ids, batch_num)


@shared_task
def fallback_batch_update(nomenclature_ids, batch_num):
    """
    Запасной метод обновления (по одной записи) в случае ошибки SQL
    """
    logger.info(f"Батч {batch_num}: использование запасного метода")
    updated = 0

    for n_id in nomenclature_ids:
        try:
            nomenclature = Nomenclature.objects.get(id=n_id)

            # Получаем данные арендаторов
            tenants_text = ' '.join(
                f"{t.tenant.first_name or ''} {t.tenant.last_name or ''} {t.tenant.additional_name or ''} {t.tenant.keyword or ''} {t.floor or ''}"
                for t in nomenclature.nomenclaturetenant_set.select_related('tenant').all()
            )

            # Обновляем search_vector
            from django.contrib.postgres.search import SearchVector
            from django.db.models import Value

            nomenclature.search_vector = (
                    SearchVector(Value(nomenclature.name or ''), weight='A') +
                    SearchVector(Value(nomenclature.contentType or ''), weight='C') +
                    SearchVector(Value(nomenclature.typeOfPlace.name if nomenclature.typeOfPlace else ''), weight='B') +
                    SearchVector(Value(nomenclature.version or ''), weight='B') +
                    SearchVector(Value(nomenclature.code1c or ''), weight='A') +
                    SearchVector(Value(nomenclature.brand.name if nomenclature.brand else ''), weight='A') +
                    SearchVector(Value(nomenclature.legalEntity.first_name if nomenclature.legalEntity else ''),
                                 weight='A') +
                    SearchVector(Value(nomenclature.legalEntity.last_name if nomenclature.legalEntity else ''),
                                 weight='B') +
                    SearchVector(Value(nomenclature.legalEntity.keyword if nomenclature.legalEntity else ''),
                                 weight='A') +
                    SearchVector(Value(nomenclature.legalEntity.additional_name if nomenclature.legalEntity else ''),
                                 weight='C') +
                    SearchVector(
                        Value(nomenclature.responsible_radio.first_name if nomenclature.responsible_radio else ''),
                        weight='A') +
                    SearchVector(Value(nomenclature.responsible_ad.first_name if nomenclature.responsible_ad else ''),
                                 weight='A') +
                    SearchVector(
                        Value(nomenclature.responsible_technic.first_name if nomenclature.responsible_technic else ''),
                        weight='A') +
                    SearchVector(Value(
                        nomenclature.responsible_technic_on_address.last_name if nomenclature.responsible_technic_on_address else ''),
                                 weight='B') +
                    SearchVector(
                        Value(nomenclature.responsible_radio.last_name if nomenclature.responsible_radio else ''),
                        weight='B') +
                    SearchVector(Value(nomenclature.responsible_ad.last_name if nomenclature.responsible_ad else ''),
                                 weight='B') +
                    SearchVector(
                        Value(nomenclature.responsible_technic.last_name if nomenclature.responsible_technic else ''),
                        weight='B') +
                    SearchVector(Value(tenants_text), weight='B')
            )

            nomenclature.search_vector_updated_at = timezone.now()
            nomenclature.save(update_fields=['search_vector', 'search_vector_updated_at'])
            updated += 1

        except Exception as e:
            logger.error(f"Батч {batch_num}: ошибка при обновлении {n_id}: {e}")

    return f"Батч {batch_num} (запасной): обновлено {updated}/{len(nomenclature_ids)}"


# ================ СТАРЫЕ ЗАДАЧИ (ОСТАВЛЯЕМ БЕЗ ИЗМЕНЕНИЙ) ================

@shared_task
def update_all_search_vectors_old(batch_size=500):
    """
    Старая версия задачи - оставлена для обратной совместимости
    """
    from django.contrib.postgres.search import SearchVector
    from django.db.models import Value
    from django.db.models.functions import Concat, Coalesce
    from django.contrib.postgres.aggregates import StringAgg

    # Получаем все номенклатуры
    qs = Nomenclature.objects.all()
    total = qs.count()

    print(f"Начинаю обновление search_vector для {total} номенклатур")

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch_ids = list(qs[start:end].values_list('id', flat=True))

        print(f"Обрабатываю номенклатуры {start + 1}-{end} из {total}")

        # Для каждой номенклатуры в батче обновляем search_vector по отдельности
        for n_id in batch_ids:
            try:
                n = Nomenclature.objects.get(id=n_id)

                # Получаем агрегированные данные по арендаторам
                tenants_agg = NomenclatureTenant.objects.filter(
                    nomenclature=n
                ).annotate(
                    tenant_text=Concat(
                        Coalesce('tenant__first_name', Value('')), Value(' '),
                        Coalesce('tenant__last_name', Value('')), Value(' '),
                        Coalesce('tenant__additional_name', Value('')), Value(' '),
                        Coalesce('tenant__keyword', Value('')), Value(' '),
                        Coalesce('floor', Value(''))
                    )
                ).aggregate(
                    all_tenants=StringAgg('tenant_text', delimiter=' ')
                )['all_tenants'] or ''

                # Обновляем search_vector
                n.search_vector = (
                        SearchVector(Value(n.name or ''), weight='A') +
                        SearchVector(Value(n.contentType or ''), weight='C') +
                        SearchVector(Value(n.typeOfPlace.name if n.typeOfPlace else ''), weight='B') +
                        SearchVector(Value(n.version or ''), weight='B') +
                        SearchVector(Value(n.code1c or ''), weight='A') +
                        SearchVector(Value(n.brand.name if n.brand else ''), weight='A') +
                        SearchVector(Value(n.legalEntity.first_name if n.legalEntity else ''), weight='A') +
                        SearchVector(Value(n.legalEntity.last_name if n.legalEntity else ''), weight='B') +
                        SearchVector(Value(n.legalEntity.keyword if n.legalEntity else ''), weight='A') +
                        SearchVector(Value(n.legalEntity.additional_name if n.legalEntity else ''), weight='C') +
                        SearchVector(Value(n.responsible_radio.first_name if n.responsible_radio else ''), weight='A') +
                        SearchVector(Value(n.responsible_ad.first_name if n.responsible_ad else ''), weight='A') +
                        SearchVector(Value(n.responsible_technic.first_name if n.responsible_technic else ''),
                                     weight='A') +
                        SearchVector(Value(
                            n.responsible_technic_on_address.last_name if n.responsible_technic_on_address else ''),
                                     weight='B') +
                        SearchVector(Value(n.responsible_radio.last_name if n.responsible_radio else ''), weight='B') +
                        SearchVector(Value(n.responsible_ad.last_name if n.responsible_ad else ''), weight='B') +
                        SearchVector(Value(n.responsible_technic.last_name if n.responsible_technic else ''),
                                     weight='B') +
                        SearchVector(Value(tenants_agg), weight='B')
                )
                n.search_vector_updated_at = timezone.now()
                n.save(update_fields=['search_vector', 'search_vector_updated_at'])

            except Exception as e:
                print(f"Ошибка при обработке номенклатуры {n_id}: {e}")
                continue

    print("Обновление search_vector завершено!")


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
                        status=ONLINE,
                        client=status.client
                    )
                )

    if statuses_to_update:
        NomenclatureAvailability.objects.bulk_update(statuses_to_update, ['status'])
    if status_histories_to_create:
        StatusHistory.objects.bulk_create(status_histories_to_create)

    return f'Обновлено {len(statuses_to_update)} статусов доступности.'


@shared_task
def resend_orders_task(nomenclature_id: int):
    """
    Переотправка заказов.
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
    if task_list:
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