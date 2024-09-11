from asyncio import current_task
from datetime import datetime, timedelta

from rmc_rest_api.celery import app
from .models import NomenclatureAvailability, StatusHistory
from celery import shared_task
from celery_singleton import Singleton

@shared_task(base=Singleton)
def update_nomenclature_status():
    """
    Обновление статусов доступности номенклатур
    и запись истории их изменения.
    """
    statuses = NomenclatureAvailability.objects.all()
    count_updated_statuses = 0
    for status in statuses:
        now_time = datetime.now()
        new_status = 0
        current_status = status.status
        last_answer = status.last_answer_date
        if current_status == 0:
            if now_time - last_answer > timedela(hoturs=1):
                new_status = 2
            elif now_time - last_answer > timedelta(minutes=5):
                new_status = 1
            if new_status != current_status:
                status.status = new_status
                status.save()
                StatusHistory.objects.create(
                    status=new_status,
                    client=status.client
                )
                count_updated_statuses += 1

        if current_status == 1:
            new_status = 1
            if now_time - last_answer > timedelta(hours=1):
                new_status = 2
            elif now_time - last_answer < timedelta(minutes=5):
                new_status = 0
            if new_status != current_status:
                status.status = new_status
                status.save()
                StatusHistory.objects.create(
                    status=new_status,
                    client=status.client
                )
                count_updated_statuses += 1

        if current_status == 2:
            if now_time - last_answer < timedelta(minutes=5):
                status.status = 0
                status.save()
                StatusHistory.objects.create(
                    status=0,
                    client=status.client
                )
                count_updated_statuses += 1
    return f"Обновлено {count_updated_statuses} статусов."
