import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'rmc_rest_api.settings')

app = Celery('rmc_rest_api')
app.config_from_object('django.conf:settings', namespace="CELERY")
app.conf.singleton_backend_url = app.conf.get('CELERY_SINGLETON_BACKEND_URL')

# Оптимизация настроек Celery для production
app.conf.update(
    worker_max_tasks_per_child=1000,  # Перезапуск воркеров после 1000 задач
    worker_max_memory_per_child=200000,  # 200MB лимит памяти на воркер
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    task_acks_late=True,  # Ack tasks after they're completed
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
)

app.autodiscover_tasks()

# Beat schedule остается без изменений
app.conf.beat_schedule = {
    'update_nomenclature_statuses_5_sec': {
        'task': 'nomenclatures.tasks.update_nomenclature_status',
        'schedule': 5.0,
    },
    'update_order_statuses_30_sec': {
        'task': 'orders.tasks.update_order_status',
        'schedule': 30.0,
    }
}
