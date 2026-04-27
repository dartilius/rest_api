# feedback/tasks.py
import logging
from email.utils import formatdate, make_msgid

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger('feedback')


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_feedback_email(self, name: str, phone: str, email: str, message: str, created: str) -> str:
    """Отправка уведомления админу"""
    task_id = self.request.id
    from_email = settings.DEFAULT_FROM_EMAIL
    logger.info(f"[TASK ADMIN {task_id}] Sending to {from_email}")

    try:
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
            from_email=from_email,
            to=[from_email],
            headers={
                "From": f"RMC <{from_email}>",
                "Date": formatdate(localtime=True),
                "Message-ID": make_msgid(domain="email.krasrm.com"),
            },
        )
        result = msg.send()
        logger.info(f"[TASK ADMIN {task_id}] ✅ Sent: {result}")
        return f"Admin notification sent for {email}"

    except Exception as e:
        logger.error(f"[TASK ADMIN {task_id}] ❌ Failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_feedback_mail(self, name: str, email: str, message: str, created: str) -> str:
    """Отправка подтверждения пользователю"""
    task_id = self.request.id
    from_email = settings.DEFAULT_FROM_EMAIL
    logger.info(f"[TASK USER {task_id}] Sending to {email}")

    try:
        msg = EmailMessage(
            subject="Мы получили ваше обращение",
            body=(
                f"Здравствуйте, {name}!\n\n"
                f"Ваше обращение принято. Мы свяжемся с вами в ближайшее время.\n\n"
                f"Текст вашего сообщения:\n{message}"
            ),
            from_email=from_email,
            to=[email],
            headers={
                "From": f"RMC <{from_email}>",
                "Date": formatdate(localtime=True),
                "Message-ID": make_msgid(domain="email.krasrm.com"),
            },
        )
        result = msg.send()
        logger.info(f"[TASK USER {task_id}] ✅ Sent: {result}")
        return f"Письмо отправлено для {email}"

    except Exception as e:
        logger.error(f"[TASK USER {task_id}] ❌ Failed: {e}")
        raise self.retry(exc=e)