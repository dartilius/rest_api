from django.db.models.signals import post_save
from django.dispatch import receiver

from feedback.models import Feedback
from feedback.tasks import send_feedback_email, send_feedback_mail


@receiver(post_save, sender=Feedback)
def on_feedback_created(sender, instance: Feedback, created: bool, **kwargs) -> None:
    if not created:
        return

    send_feedback_email.delay(
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
    send_feedback_mail(
        name=instance.name,
        phone=instance.phone,
        email=instance.email,
        message=instance.message,
        created=instance.created.strftime("%d.%m.%Y %H:%M"),
    )
