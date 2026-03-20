import os

from rmc_rest_api import settings
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'rmc_rest_api.settings')

app = Celery('rmc_rest_api')
app.config_from_object('django.conf:settings', namespace="CELERY")
app.conf.singleton_backend_url = settings.CELERY_SINGLETON_BACKEND_URL
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'update_nomenclature_statuses_5_sec': {
        'task': 'nomenclatures.tasks.update_nomenclature_status',
        'schedule': 5.0,
    },
    'update_order_statuses_30_sec': {
        'task': 'orders.tasks.update_order_status',
        'schedule': 30.0,
#     },
#     'update_nomenclature_search_vectors': {
#         'task': 'nomenclatures.tasks.update_all_search_vectors',
#         'schedule': crontab(hour=3, minute=0),
#     }
# }
