# feedback/tasks.py
import logging
from celery import shared_task
from django.core.mail import EmailMessage

logger = logging.getLogger('feedback')
email_logger = logging.getLogger('feedback.email')


@shared_task
def send_feedback_email(name: str, phone: str, email: str, message: str, created: str) -> str:
    """Отправка уведомления админу"""

    logger.info(f"[TASK ADMIN] Starting for user: {email}")
    print(f"[TASK ADMIN] Sending email to info@krasrm.com from {email}")

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

        logger.info(f"[TASK ADMIN] ✅ Sent successfully")
        email_logger.info(f"ADMIN_EMAIL_SENT: to=info@krasrm.com from_user={email}")
        return f"Admin notification sent for {email}"

    except Exception as e:
        logger.error(f"[TASK ADMIN] ❌ Failed: {e}")
        email_logger.error(f"ADMIN_EMAIL_FAILED: error={e}")
        raise


@shared_task
def send_feedback_mail(name: str, email: str, message: str, created: str) -> str:
    """Отправка подтверждения пользователю"""

    logger.info(f"[TASK USER] Starting for: {email}")
    print(f"[TASK USER] Sending confirmation to {email}")

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

        logger.info(f"[TASK USER] ✅ Sent successfully to {email}")
        email_logger.info(f"USER_EMAIL_SENT: to={email}")
        return f"Письма отправлены для {email}"

    except Exception as e:
        logger.error(f"[TASK USER] ❌ Failed for {email}: {e}")
        email_logger.error(f"USER_EMAIL_FAILED: to={email} error={e}")
        raise