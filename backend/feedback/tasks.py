from celery import shared_task
from django.core.mail import EmailMessage

from rmc_rest_api.settings import DEFAULT_FROM_EMAIL


@shared_task
def send_feedback_email(name: str, phone: str, email: str, message: str, created: str) -> str:
    msg = EmailMessage(
        subject="Новое обращение с сайта",
        body=(
            f"Получено новое обращение:\n\n"
            f"Имя:     {name}\n"
            f"Телефон: {phone}\n"
            f"Почта:   {email}\n"
            f"Дата:    {created}\n\n"
            f"Сообщение:\n{message}"
        ),
        from_email="info@krasrm.com",
        to=["info@krasrm.com"],
    )
    msg.send()
    return f"Admin notification sent for {email}"

@shared_task
def send_feedback_mail(name: str, email: str, message: str, created: str) -> str:
    msg = EmailMessage(
        subject="Мы получили ваше обращение",
        body=(
            f"Здравствуйте, {name}!\n\n"
            f"Ваше обращение принято. Мы свяжемся с вами в ближайшее время.\n\n"
            f"Текст вашего сообщения:\n{message}"
        ),
        to=[email],
    )
    msg.send()
    return f"notification sent for {email}"