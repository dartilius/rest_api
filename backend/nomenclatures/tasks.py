from datetime import datetime, timedelta
from celery import shared_task
from celery_singleton import Singleton

from nomenclatures.models import NomenclatureAvailability, StatusHistory


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

    NomenclatureAvailability.objects.bulk_update(statuses_to_update, ["status"])
    StatusHistory.objects.bulk_create(status_histories_to_create)

    return f"Обновлено {len(statuses_to_update)} статусов доступности."
