import threading

from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from feedback.models import Feedback
from rmc_rest_api.settings import DEFAULT_FROM_EMAIL


def _send_feedback_email(feedback: Feedback) -> None:
    """Отправляет уведомление администраторам и подтверждение пользователю."""

    send_mail(
        subject="Новое обращение с сайта",
        message=(
            f"Получено новое обращение:\n\n"
            f"Имя:     {feedback.name}\n"
            f"Телефон: {feedback.phone}\n"
            f"Почта:   {feedback.email}\n"
            f"Дата:    {feedback.created:%d.%m.%Y %H:%M}\n\n"
            f"Сообщение:\n{feedback.message}"
        ),
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[DEFAULT_FROM_EMAIL],
        fail_silently=False,
    )

    # Подтверждение пользователю
    send_mail(
        subject="Мы получили ваше обращение",
        message=(
            f"Здравствуйте, {feedback.name}!\n\n"
            f"Ваше обращение принято. Мы свяжемся с вами в ближайшее время.\n\n"
            f"Текст вашего сообщения:\n{feedback.message}"
        ),
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[feedback.email],
        fail_silently=False,
    )


@receiver(post_save, sender=Feedback)
def on_feedback_created(sender, instance: Feedback, created: bool, **kwargs) -> None:
    """Запускает рассылку в отдельном потоке, чтобы не блокировать запрос."""
    if not created:
        return

    thread = threading.Thread(
        target=_send_feedback_email,
        args=(instance,),
        daemon=True,
    )
    thread.start()