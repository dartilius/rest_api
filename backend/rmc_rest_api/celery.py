import os
import logging
from logging.handlers import RotatingFileHandler

from rmc_rest_api import settings
from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_logger, after_setup_task_logger

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'rmc_rest_api.settings')

app = Celery('rmc_rest_api')
app.config_from_object('django.conf:settings', namespace="CELERY")
app.conf.singleton_backend_url = settings.CELERY_SINGLETON_BACKEND_URL
app.autodiscover_tasks()

# Создаем директорию для логов
LOG_DIR = os.path.join(settings.BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)


@after_setup_logger.connect
def setup_celery_logger(logger, *args, **kwargs):
    """Настройка основного логгера Celery"""
    logger.handlers.clear()  # Очищаем стандартные handlers

    # Форматтер для логов
    formatter = logging.Formatter(
        '[%(levelname)s] %(asctime)s | CELERY | %(processName)s-%(threadName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (для вывода в консоль)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (запись в файл)
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'celery.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Отдельный файл для ошибок
    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'celery_errors.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    logger.setLevel(logging.INFO)
    logger.info("=" * 60)
    logger.info("Celery logger initialized")
    logger.info("=" * 60)


@after_setup_task_logger.connect
def setup_celery_task_logger(logger, *args, **kwargs):
    """Настройка логгера для задач"""
    # Используем тот же форматтер
    formatter = logging.Formatter(
        '[%(levelname)s] %(asctime)s | CELERY TASK | %(task_name)s | %(task_id)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler для задач
    task_file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'celery_tasks.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    task_file_handler.setFormatter(formatter)
    logger.addHandler(task_file_handler)

    logger.setLevel(logging.DEBUG)


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