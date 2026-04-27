from celery import shared_task
from django.core.mail import EmailMessage

from rmc_rest_api.settings import DEFAULT_FROM_EMAIL


@shared_task
def send_feedback_email(name: str, phone: str, email: str, message: str, created: str) -> str:
    from_email = DEFAULT_FROM_EMAIL

    EmailMessage(
        subject="Новое обращение с сайта",
        body=(
            f"Получено новое обращение:\n\n"
            f"Имя:     {name}\n"
            f"Телефон: {phone}\n"
            f"Почта:   {email}\n"
            f"Дата:    {created}\n\n"
            f"Сообщение:\n{message}"
        ),
        from_email=from_email,
        to=[from_email],
    ).send()

    EmailMessage(
        subject="Мы получили ваше обращение",
        body=(
            f"Здравствуйте, {name}!\n\n"
            f"Ваше обращение принято. Мы свяжемся с вами в ближайшее время.\n\n"
            f"Текст вашего сообщения:\n{message}"
        ),
        from_email=from_email,
        to=[from_email],
    ).send()

    return f"Письма отправлены для {email}"