from datetime import datetime, timedelta

from rmc_rest_api.celery import app
from .models import NomenclatureAvailability, StatusHistory
from celery import shared_task

@shared_task
def update_nomenclature_status():
    """
    Обновление статусов доступности номенклатур
    и запись истории их изменения.
    """
    statuses = NomenclatureAvailability.objects.all()

    for status in statuses:
        now_time = datetime.now()
        new_status = 0
        if status.status == 0:
            if now_time - status.last_answer_date > timedelta(hours=1):
                new_status = 2
            elif now_time - status.last_answer_date > timedelta(minutes=5):
                new_status = 1
            if new_status:
                status.status = new_status
                status.save()
                StatusHistory.objects.create(
                    status=new_status,
                    client=status.client
                )

        if status.status == 1:
            if now_time - status.last_answer_date > timedelta(hours=1):
                new_status = 2
            elif now_time - status.last_answer_date < timedelta(minutes=5):
                new_status = 0
            if new_status != 1:
                status.status = new_status
                status.save()
                StatusHistory.objects.create(
                    status=new_status,
                    client=status.client
                )

        if status.status == 2:
            if now_time - status.last_answer_date < timedelta(minutes=5):
                status.status = 0
                status.save()
                StatusHistory.objects.create(
                    status=0,
                    client=status.client
                )
    return 0