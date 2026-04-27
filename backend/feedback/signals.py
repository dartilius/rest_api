from django.db.models.signals import post_save
from django.dispatch import receiver

from feedback.models import Feedback
from feedback.tasks import send_feedback_email, send_feedback_mail

import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Feedback)
def on_feedback_created(sender, instance: Feedback, created: bool, **kwargs) -> None:
    if not created:
        return

    # Защита от повторной отправки
    if hasattr(instance, '_email_sent_to_admin'):
        logger.warning(f"Email to admin already sent for feedback {instance.id}")
        return

    instance._email_sent_to_admin = True

    logger.info(f"Sending admin notification for feedback {instance.id}")
    send_feedback_email(
        name=instance.name,
        phone=instance.phone,
        email=instance.email,
        message=instance.message,
        created=instance.created.strftime("%d.%m.%Y %H:%M"),
    )


@receiver(post_save, sender=Feedback)
def on_feedback_user(sender, instance: Feedback, created: bool, **kwargs) -> None:
    if not created:
        return

    # Защита от повторной отправки
    if hasattr(instance, '_email_sent_to_user'):
        logger.warning(f"User email already sent for feedback {instance.id}")
        return

    instance._email_sent_to_user = True

    logger.info(f"Sending user confirmation for feedback {instance.id}")
    send_feedback_mail(
        name=instance.name,
        email=instance.email,
        message=instance.message,
        created=instance.created.strftime("%d.%m.%Y %H:%M"),
    )