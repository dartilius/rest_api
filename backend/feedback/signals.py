# feedback/signals.py
import logging
from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver

from feedback.models import Feedback
from feedback.tasks import send_feedback_email, send_feedback_mail

# Создаем логгеры
logger = logging.getLogger('feedback')
email_logger = logging.getLogger('feedback.email')


@receiver(post_save, sender=Feedback)
def on_feedback_created(sender, instance: Feedback, created: bool, **kwargs) -> None:
    """Отправка уведомления админу о новом обращении"""

    logger.info(f"[СИГНАЛ 1] Вызван on_feedback_created | id={instance.id} | created={created}")

    if not created:
        logger.debug(f"[СИГНАЛ 1] Пропуск: объект уже существует (created=False) | id={instance.id}")
        return

    logger.info(f"[СИГНАЛ 1] Создаем задачу для отправки админу | id={instance.id}")
    logger.debug(f"[СИГНАЛ 1] Данные: name={instance.name}, email={instance.email}, phone={instance.phone}")

    try:
        task = send_feedback_email.delay(
            name=instance.name,
            phone=instance.phone,
            email=instance.email,
            message=instance.message,
            created=instance.created.strftime("%d.%m.%Y %H:%M"),
        )
        logger.info(f"[СИГНАЛ 1] Задача создана успешно | task_id={task.id}")
        email_logger.info(f"ADMIN EMAIL TASK CREATED | feedback_id={instance.id} | task_id={task.id}")
    except Exception as e:
        logger.error(f"[СИГНАЛ 1] Ошибка создания задачи: {e}")
        email_logger.error(f"FAILED TO CREATE ADMIN EMAIL TASK | feedback_id={instance.id} | error={e}")


@receiver(post_save, sender=Feedback)
def on_feedback_user(sender, instance: Feedback, created: bool, **kwargs) -> None:
    """Отправка подтверждения пользователю"""

    logger.info(f"[СИГНАЛ 2] Вызван on_feedback_user | id={instance.id} | created={created}")

    if not created:
        logger.debug(f"[СИГНАЛ 2] Пропуск: объект уже существует (created=False) | id={instance.id}")
        return

    logger.info(f"[СИГНАЛ 2] Создаем задачу для отправки пользователю | id={instance.id}")

    try:
        task = send_feedback_mail.delay(
            name=instance.name,
            email=instance.email,
            message=instance.message,
            created=instance.created.strftime("%d.%m.%Y %H:%M"),
        )
        logger.info(f"[СИГНАЛ 2] Задача создана успешно | task_id={task.id}")
        email_logger.info(
            f"USER EMAIL TASK CREATED | feedback_id={instance.id} | user_email={instance.email} | task_id={task.id}")
    except Exception as e:
        logger.error(f"[СИГНАЛ 2] Ошибка создания задачи: {e}")
        email_logger.error(f"FAILED TO CREATE USER EMAIL TASK | feedback_id={instance.id} | error={e}")