import logging
import re
from datetime import timedelta
from itertools import chain

from celery import shared_task
from celery_singleton import Singleton
from django.utils import timezone

from api.constants import get_minio_client
from nomenclatures.models import NomenclatureAvailability, StatusHistory, Nomenclature
from orders.models import AdOrder, BgOrder
from tasks.models import Task
from users.models import CustomUser


logger = logging.getLogger(__name__)
INDEX_RETRY_DELAY_SECONDS = 30
UPDATE_RETRY_DELAY_SECONDS = 60


@shared_task(bind=True, base=Singleton, max_retries=3)
def update_opensearch_for_instance(self, instance_id):
    """Обновление документа в OpenSearch для конкретной номенклатуры."""
    try:
        from nomenclatures.documents import NomenclatureDocument
        from nomenclatures.models import Nomenclature

        nomenclature = (
            Nomenclature.objects.select_related(
                "brand",
                "legalEntity",
                "typeOfPlace",
                "responsible_radio",
                "responsible_ad",
                "responsible_technic",
                "responsible_technic_on_address",
                "responsible_placement_marketing",
            )
            .prefetch_related(
                "nomenclature_tenants__tenant",
                "nomenclature_tenants__brand",
            )
            .get(id=instance_id)
        )

        NomenclatureDocument().index(nomenclature)
        logger.info("OpenSearch updated for nomenclature %s", instance_id)
    except Nomenclature.DoesNotExist:
        logger.info("Nomenclature %s no longer exists; indexing is not required", instance_id)
    except Exception as exc:
        logger.exception("OpenSearch indexing failed for nomenclature %s", instance_id)
        raise self.retry(exc=exc, countdown=INDEX_RETRY_DELAY_SECONDS)


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
                    StatusHistory(status=new_status, client=status.client)
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
                    StatusHistory(status=new_status, client=status.client)
                )

        if current_status == OFFLINE_1_HOUR:
            if now_time - last_answer < timedelta(minutes=5):
                status.status = ONLINE
                statuses_to_update.append(status)
                status_histories_to_create.append(
                    StatusHistory(status=new_status, client=status.client)
                )

    NomenclatureAvailability.objects.bulk_update(statuses_to_update, ["status"])
    StatusHistory.objects.bulk_create(status_histories_to_create)

    return f"Обновлено {len(statuses_to_update)} статусов доступности."


@shared_task
def resend_orders_task(nomenclature_id: int):
    """
    Переотправка заказов.

    Использует f-string для получения времени (как в старой версии),
    чтобы избежать проблем с часовым поясом.

    Аргументы:
        nomenclature_id (int): ID номенклатуры для переотправки заказов

    Returns:
        str: Сообщение с количеством переотправленных заказов
    """
    task_list = []
    AD = 4

    orders = chain(
        AdOrder.objects.filter(client=nomenclature_id, status__in=[0, 1]),
        BgOrder.objects.filter(client=nomenclature_id, status__in=[0, 1]),
    )

    for order in orders:
        # Используем f-string для времени (без strftime, чтобы избежать проблем с часовым поясом)
        broadcast_start = (
            f"{order.broadcast_interval.lower}"
            if order.broadcast_interval and order.broadcast_interval.lower
            else None
        )
        broadcast_end = (
            f"{order.broadcast_interval.upper}"
            if order.broadcast_interval and order.broadcast_interval.upper
            else None
        )

        parameters = {
            "order_id": str(order.id),
            "responsible": order.owner.full_name if order.owner else None,
            "broadcast_start": broadcast_start,
            "broadcast_end": broadcast_end,
            "playlist": {
                "id": str(order.playlist.id),
                "files": [
                    {"id": str(file.id), "hash": file.hash}
                    for file in order.playlist.files.all()
                ],
            },
        }

        if isinstance(order, AdOrder):
            parameters.update(
                {
                    "order_parameters": order.parameters,
                    "broadcast_type": order.broadcast_type,
                }
            )
            parameters["playlist"]["slides"] = order.slides if order.slides else None
            task_type = AD
        else:
            parameters.update(
                {
                    "order_type": order.order_type,
                    "is_permanent": order.is_permanent,
                }
            )
            task_type = order.order_type

        task_list.append(
            Task(
                owner=order.owner,
                client=order.client,
                type=task_type,
                parameters=parameters,
            )
        )

    Task.objects.bulk_create(task_list)
    return f"Переотправленно заказов: {len(task_list)}."


@shared_task
def reboot_task(nomenclature_id: str, owner_id: str):
    """Отправка команды перезагрузки на устройство."""
    nomenclature = get_nomenclature(nomenclature_id)
    owner = get_owner(owner_id)
    Task.objects.create(
        owner=owner,
        client=nomenclature,
        type=15,
        parameters={"responsible": owner.full_name},
    )
    return f"Перезагрузка отправлена на {nomenclature.name}"


BUILD_BUCKET = "builds"
BUILD_PREFIX = "RMCContentPlayer-"
BUILD_SUFFIX = ".exe"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@shared_task(bind=True, max_retries=3)
def update_task(self, nomenclature_id: str, owner_id: str):
    """
    Создаёт задачу обновления ПО.

    Выбирает последнюю числовую версию из MinIO, получает SHA-256
    из metadata EXE и создаёт задачу type=16.

    При отсутствии сборок, SHA-256 или при ошибке пустая задача
    обновления не создаётся.
    """
    nomenclature = None

    try:
        nomenclature = get_nomenclature(nomenclature_id)
        owner = get_owner(owner_id)

        minio_client = get_minio_client()

        available_versions = []

        objects = minio_client.list_objects(
            BUILD_BUCKET,
            prefix=BUILD_PREFIX,
            recursive=False,
        )

        for item in objects:
            object_name = item.object_name

            if not (
                object_name.startswith(BUILD_PREFIX)
                and object_name.endswith(BUILD_SUFFIX)
            ):
                continue

            version = object_name[len(BUILD_PREFIX) : -len(BUILD_SUFFIX)]

            # Разрешены версии вида 1, 1.2, 1.2.3 и т.д.
            if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version):
                continue

            version_key = tuple(int(part) for part in version.split("."))

            available_versions.append((version_key, version, object_name))

        if not available_versions:
            return "Нет доступных версий для обновления " f"на {nomenclature.name}"

        _, latest_version, object_name = max(
            available_versions,
            key=lambda item: item[0],
        )

        # Получаем размер и custom metadata объекта.
        object_info = minio_client.stat_object(
            BUILD_BUCKET,
            object_name,
        )

        raw_metadata = getattr(object_info, "metadata", {}) or {}

        metadata = {
            str(key).strip().lower(): str(value).strip()
            for key, value in raw_metadata.items()
        }

        # mc cp --attr "sha256=..." сохраняет значение как
        # пользовательскую S3 metadata x-amz-meta-sha256.
        sha256 = (
            metadata.get("x-amz-meta-sha256") or metadata.get("sha256") or ""
        ).lower()

        if not SHA256_PATTERN.fullmatch(sha256):
            return f"Для версии {latest_version} " "не найден корректный SHA-256"

        external_client = get_minio_client(external=True)

        version_url = external_client.get_presigned_url(
            "GET",
            BUILD_BUCKET,
            object_name,
            expires=timedelta(hours=24),
        )

        Task.objects.create(
            owner=owner,
            client=nomenclature,
            type=16,
            parameters={
                "responsible": owner.full_name,
                "url": version_url,
                "version": latest_version,
                "sha256": sha256,
                "size": object_info.size,
                "object_name": object_name,
            },
        )

        return f"Обновление {latest_version} " f"отправлено на {nomenclature.name}"

    except Exception as exc:
        logger.exception(
            "Failed to create software-update task for nomenclature %s",
            nomenclature_id,
        )
        raise self.retry(exc=exc, countdown=UPDATE_RETRY_DELAY_SECONDS)


@shared_task
def custom_task(nomenclature_id: str, parameters: str, owner_id: str):
    """
    Отправка пользовательской команды на устройство.

    Поддерживает как строку, так и JSON объект.
    """
    nomenclature = get_nomenclature(nomenclature_id)
    owner = get_owner(owner_id)

    import json

    try:
        params_dict = (
            json.loads(parameters) if isinstance(parameters, str) else parameters
        )
    except:
        params_dict = {"command": parameters}

    params_dict["responsible"] = owner.full_name

    Task.objects.create(
        owner=owner, client=nomenclature, type=17, parameters=params_dict
    )
    return f"SH команда отправлена на {nomenclature.name}"


@shared_task
def settings_task(nomenclature_id: str, owner_id: str):
    """Отправка настроек вещания на устройство."""
    nomenclature = get_nomenclature(nomenclature_id)
    owner = get_owner(owner_id)
    Task.objects.create(
        owner=owner,
        client=nomenclature,
        type=18,
        parameters={"settings": nomenclature.settings, "responsible": owner.full_name},
    )
    return f"Настройки вещания отправлены на {nomenclature.name}"
