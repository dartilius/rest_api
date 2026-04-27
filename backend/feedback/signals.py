# feedback/signals.py
import logging
import os
from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver

from feedback.models import Feedback
from feedback.tasks import send_feedback_email, send_feedback_mail

logger = logging.getLogger('feedback')
email_logger = logging.getLogger('feedback.email')


@receiver(post_save, sender=Feedback)
def on_feedback_created(sender, instance: Feedback, created: bool, **kwargs) -> None:
    """Отправка уведомления админу о новом обращении"""

    # Принудительная запись в файл для проверки
    log_message = f"[{datetime.now()}] SIGNAL 1 CALLED | id={instance.id} | created={created}"
    print(log_message)  # Вывод в консоль

    logger.info(f"[СИГНАЛ 1] Feedback id={instance.id} created={created}")

    if not created:
        logger.info(f"[СИГНАЛ 1] SKIPPED - not created")
        return

    logger.info(f"[СИГНАЛ 1] Creating admin email task for {instance.email}")

    try:
        task = send_feedback_email.delay(
            name=instance.name,
            phone=instance.phone,
            email=instance.email,
            message=instance.message,
            created=instance.created.strftime("%d.%m.%Y %H:%M"),
        )
        logger.info(f"[СИГНАЛ 1] Task created: {task.id}")
        email_logger.info(f"ADMIN_EMAIL_TASK: feedback_id={instance.id} task_id={task.id}")
    except Exception as e:
        logger.error(f"[СИГНАЛ 1] FAILED: {e}")


@receiver(post_save, sender=Feedback)
def on_feedback_user(sender, instance: Feedback, created: bool, **kwargs) -> None:
    """Отправка подтверждения пользователю"""

    # Принудительная запись для проверки
    log_message = f"[{datetime.now()}] SIGNAL 2 CALLED | id={instance.id} | created={created}"
    print(log_message)  # Вывод в консоль

    logger.info(f"[СИГНАЛ 2] Feedback id={instance.id} created={created}")

    if not created:
        logger.info(f"[СИГНАЛ 2] SKIPPED - not created")
        return

    logger.info(f"[СИГНАЛ 2] Creating user email task for {instance.email}")

    try:
        task = send_feedback_mail.delay(
            name=instance.name,
            email=instance.email,
            message=instance.message,
            created=instance.created.strftime("%d.%m.%Y %H:%M"),
        )
        logger.info(f"[СИГНАЛ 2] Task created: {task.id}")
        email_logger.info(f"USER_EMAIL_TASK: feedback_id={instance.id} user_email={instance.email} task_id={task.id}")
    except Exception as e:
        logger.error(f"[СИГНАЛ 2] FAILED: {e}")