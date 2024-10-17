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
    count_updated_statuses = 0
    count_to_update_and_create = 0
    update_and_create_threshold = 10
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
                count_updated_statuses += 1
                count_to_update_and_create += 1

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
                count_updated_statuses += 1
                count_to_update_and_create += 1

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
                count_updated_statuses += 1
                count_to_update_and_create += 1

        if count_to_update_and_create >= update_and_create_threshold:
            NomenclatureAvailability.objects.bulk_update(statuses_to_update)
            StatusHistory.objects.bulk_create(status_histories_to_create)
            count_to_update_and_create = 0

    return f"Обновлено {count_updated_statuses} статусов доступности."
