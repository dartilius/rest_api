# feedback/signals.py
import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from feedback.models import Feedback
from feedback.tasks import send_feedback_email, send_feedback_mail

logger = logging.getLogger('feedback')
email_logger = logging.getLogger('feedback.email')


def _enqueue(task, *, feedback_id, **kwargs) -> None:
    """Queue Celery work only after the feedback row has committed."""
    def enqueue() -> None:
        try:
            result = task.delay(**kwargs)
            email_logger.info("FEEDBACK_EMAIL_TASK: feedback_id=%s task_id=%s", feedback_id, result.id)
        except Exception:
            logger.exception("Could not enqueue feedback notification for %s", feedback_id)

    transaction.on_commit(enqueue)


@receiver(post_save, sender=Feedback)
def on_feedback_created(sender, instance: Feedback, created: bool, **kwargs) -> None:
    """Отправка уведомления админу о новом обращении"""

    logger.info(f"[СИГНАЛ 1] Feedback id={instance.id} created={created}")

    if not created:
        logger.info(f"[СИГНАЛ 1] SKIPPED - not created")
        return

    logger.info(f"[СИГНАЛ 1] Creating admin email task for {instance.email}")

    _enqueue(
        send_feedback_email,
        feedback_id=instance.id,
        name=instance.name,
        phone=instance.phone,
        email=instance.email,
        message=instance.message,
        created=instance.created.strftime("%d.%m.%Y %H:%M"),
        pathname=instance.pathname,
        brand_id=instance.brand_id,
        nomenclatures_ids=instance.nomenclatures_ids,
    )


@receiver(post_save, sender=Feedback)
def on_feedback_user(sender, instance: Feedback, created: bool, **kwargs) -> None:
    """Отправка подтверждения пользователю"""

    logger.info(f"[СИГНАЛ 2] Feedback id={instance.id} created={created}")

    if not created:
        logger.info(f"[СИГНАЛ 2] SKIPPED - not created")
        return

    if not instance.email:
        logger.info(f"[СИГНАЛ 2] SKIPPED - no email")
        return

    logger.info(f"[СИГНАЛ 2] Creating user email task for {instance.email}")

    _enqueue(
        send_feedback_mail,
        feedback_id=instance.id,
        name=instance.name,
        email=instance.email,
        message=instance.message,
        created=instance.created.strftime("%d.%m.%Y %H:%M"),
        pathname=instance.pathname,
        brand_id=instance.brand_id,
        nomenclatures_ids=instance.nomenclatures_ids,
    )
