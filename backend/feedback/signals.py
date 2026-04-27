import threading

from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from feedback.models import Feedback
from rmc_rest_api.settings import DEFAULT_FROM_EMAIL
from django.core.mail import get_connection, EmailMessage

def _send_feedback_email(feedback: Feedback) -> None:
    with get_connection() as connection:
        connection.open()
        messages = [
            EmailMessage(
                subject="Новое обращение с сайта",
                body=(
                    f"Получено новое обращение:\n\n"
                    f"Имя:     {feedback.name}\n"
                    f"Телефон: {feedback.phone}\n"
                    f"Почта:   {feedback.email}\n"
                    f"Дата:    {feedback.created:%d.%m.%Y %H:%M}\n\n"
                    f"Сообщение:\n{feedback.message}"
                ),
                from_email=DEFAULT_FROM_EMAIL,
                to=[DEFAULT_FROM_EMAIL],
                connection=connection,
            ),
            EmailMessage(
                subject="Мы получили ваше обращение",
                body=(
                    f"Здравствуйте, {feedback.name}!\n\n"
                    f"Ваше обращение принято. Мы свяжемся с вами в ближайшее время.\n\n"
                    f"Текст вашего сообщения:\n{feedback.message}"
                ),
                from_email=DEFAULT_FROM_EMAIL,
                to=[feedback.email],
                connection=connection,
            ),
        ]
        connection.send_messages(messages)


@receiver(post_save, sender=Feedback)
def on_feedback_created(sender, instance: Feedback, created: bool, **kwargs) -> None:
    if not created:
        return
    _send_feedback_email(instance)