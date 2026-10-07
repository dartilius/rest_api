import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from feedback.models import Feedback
from feedback.tasks import send_feedback_email, send_feedback_mail

logger = logging.getLogger("feedback")


def _enqueue(task, *, feedback_id, **kwargs):
    def enqueue():
        try:
            task.delay(**kwargs)
            logger.info("Feedback notification queued: id=%s task=%s", feedback_id, task.name)
        except Exception as exc:
            # The saved request remains visible to staff if the broker is down.
            logger.error("Feedback notification queue failed: id=%s error=%s", feedback_id, type(exc).__name__)
    transaction.on_commit(enqueue)


def _notification_data(instance):
    return dict(name=instance.name, email=instance.email, message=instance.message,
                created=instance.created.strftime("%d.%m.%Y %H:%M"), pathname=instance.pathname,
                brand_id=instance.brand_id, nomenclatures_ids=instance.nomenclatures_ids,
                request_type=instance.request_type, company=instance.company,
                request_data=instance.request_data, request_id=str(instance.id))


@receiver(post_save, sender=Feedback)
def on_feedback_created(sender, instance, created, **kwargs):
    if created:
        _enqueue(send_feedback_email, feedback_id=instance.id, phone=instance.phone, **_notification_data(instance))


@receiver(post_save, sender=Feedback)
def on_feedback_user(sender, instance, created, **kwargs):
    if created and instance.email:
        _enqueue(send_feedback_mail, feedback_id=instance.id, **_notification_data(instance))
