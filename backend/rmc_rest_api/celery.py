import os

from django.conf import settings
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'rmc_rest_api.settings')

app = Celery('rmc_rest_api')
app.config_from_object('django.conf:settings', namespace="CELERY")
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.singleton_backend_url = settings.CELERY_SINGLETON_BACKEND_URL
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'update_nomenclature_statuses_5_sec': {
        'task': 'nomenclatures.tasks.update_nomenclature_status',
        'schedule': 5.0,
    }
}
