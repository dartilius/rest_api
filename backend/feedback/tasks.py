# feedback/tasks.py
import logging
from datetime import datetime
from celery import shared_task
from django.core.mail import EmailMessage, get_connection

logger = logging.getLogger('feedback')


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_feedback_email(self, name: str, phone: str, email: str, message: str, created: str) -> str:
    """Отправка уведомления админу"""

    task_id = self.request.id
    logger.info(f"[TASK ADMIN {task_id}] Sending to info@krasrm.com")

    try:
        # Создаем соединение с нашим кастомным бэкендом
        connection = get_connection(
            backend='feedback.email_backend.CustomEmailBackend',
            fail_silently=False,
        )

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
            connection=connection,  # Используем наше соединение
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
    logger.info(f"[TASK USER {task_id}] Sending to {email}")

    try:
        connection = get_connection(
            backend='feedback.email_backend.CustomEmailBackend',
            fail_silently=False,
        )

        msg = EmailMessage(
            subject="Мы получили ваше обращение",
            body=(
                f"Здравствуйте, {name}!\n\n"
                f"Ваше обращение принято. Мы свяжемся с вами в ближайшее время.\n\n"
                f"Текст вашего сообщения:\n{message}"
            ),
            to=[email],
            connection=connection,
        )

        result = msg.send()
        logger.info(f"[TASK USER {task_id}] ✅ Sent: {result}")
        return f"Письмо отправлено для {email}"

    except Exception as e:
        logger.error(f"[TASK USER {task_id}] ❌ Failed: {e}")
        raise self.retry(exc=e)