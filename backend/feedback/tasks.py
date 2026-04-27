# feedback/tasks.py
import logging
from datetime import datetime

from celery import shared_task
from django.core.mail import EmailMessage

# Логгеры
logger = logging.getLogger('feedback')
email_logger = logging.getLogger('feedback.email')


@shared_task(bind=True, max_retries=3)
def send_feedback_email(self, name: str, phone: str, email: str, message: str, created: str) -> str:
    """Отправка уведомления админу"""

    task_id = self.request.id
    logger.info(f"[TASK ADMIN] Начало выполнения | task_id={task_id} | from={email}")
    email_logger.info(f"EXECUTING ADMIN EMAIL | task_id={task_id} | to=info@krasrm.com | from_user={email}")

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
            from_email="info@krasrm.com",
            to=["info@krasrm.com"],
        )
        msg.send()

        logger.info(f"[TASK ADMIN] ✅ Письмо успешно отправлено | task_id={task_id}")
        email_logger.info(f"ADMIN EMAIL SENT | task_id={task_id} | to=info@krasrm.com | status=success")
        return f"Admin notification sent for {email}"

    except Exception as e:
        logger.error(f"[TASK ADMIN] ❌ Ошибка отправки | task_id={task_id} | error={e}")
        email_logger.error(f"ADMIN EMAIL FAILED | task_id={task_id} | error={e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_feedback_mail(self, name: str, email: str, message: str, created: str) -> str:
    """Отправка подтверждения пользователю"""

    task_id = self.request.id
    logger.info(f"[TASK USER] Начало выполнения | task_id={task_id} | to={email}")
    email_logger.info(f"EXECUTING USER EMAIL | task_id={task_id} | to={email}")

    try:
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

        logger.info(f"[TASK USER] ✅ Письмо пользователю отправлено | task_id={task_id} | to={email}")
        email_logger.info(f"USER EMAIL SENT | task_id={task_id} | to={email} | status=success")
        return f"Письма отправлены для {email}"

    except Exception as e:
        logger.error(f"[TASK USER] ❌ Ошибка отправки | task_id={task_id} | to={email} | error={e}")
        email_logger.error(f"USER EMAIL FAILED | task_id={task_id} | to={email} | error={e}")
        raise self.retry(exc=e, countdown=60)