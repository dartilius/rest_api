import os
from rmc_rest_api import settings
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'rmc_rest_api.settings')

app = Celery('rmc_rest_api')
app.config_from_object('django.conf:settings', namespace="CELERY")
app.conf.singleton_backend_url = settings.CELERY_SINGLETON_BACKEND_URL

# Настройка маршрутизации задач
app.conf.task_routes = {
    'nomenclatures.tasks.schedule_incremental_update': {'queue': 'heavy_tasks'},
    'nomenclatures.tasks.update_search_vectors_batch': {'queue': 'heavy_tasks'},
    'nomenclatures.tasks.full_update_all_search_vectors': {'queue': 'heavy_tasks'},
    'nomenclatures.tasks.full_update_batch': {'queue': 'heavy_tasks'},
    'nomenclatures.tasks.fallback_batch_update': {'queue': 'heavy_tasks'},
}

# Настройки для долгих задач
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.task_track_started = True
app.conf.task_time_limit = 10800  # 3 часа
app.conf.task_soft_time_limit = 7200  # 2 часа

app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Быстрые задачи (каждые 5-30 секунд)
    'update_nomenclature_statuses_5_sec': {
        'task': 'nomenclatures.tasks.update_nomenclature_status',
        'schedule': 5.0,
        'options': {'queue': 'celery'}
    },
    'update_order_statuses_30_sec': {
        'task': 'orders.tasks.update_order_status',
        'schedule': 30.0,
        'options': {'queue': 'celery'}
    },

    # Инкрементальное обновление поисковых векторов (каждые 6 часов)
    'update_nomenclature_search_vectors_incremental_6h': {
        'task': 'nomenclatures.tasks.schedule_incremental_update',
        'schedule': crontab(hour='*/6', minute=0),  # Каждые 6 часов
        'kwargs': {'hours': 24, 'batch_size': 100},
        'options': {'queue': 'heavy_tasks'}
    },

    # Дополнительное инкрементальное обновление (каждые 30 минут для срочных изменений)
    'update_nomenclature_search_vectors_incremental_30min': {
        'task': 'nomenclatures.tasks.schedule_incremental_update',
        'schedule': crontab(minute='*/30'),  # Каждые 30 минут
        'kwargs': {'hours': 1, 'batch_size': 50},
        'options': {'queue': 'heavy_tasks'}
    },

    # ПОЛНОЕ ОБНОВЛЕНИЕ (раз в неделю в воскресенье в 3:00)
    'update_nomenclature_search_vectors_full_weekly': {
        'task': 'nomenclatures.tasks.full_update_all_search_vectors',
        'schedule': crontab(hour=3, minute=0, day_of_week='sun'),  # Воскресенье 3:00
        'kwargs': {'batch_size': 200},
        'options': {'queue': 'heavy_tasks'}
    },
}