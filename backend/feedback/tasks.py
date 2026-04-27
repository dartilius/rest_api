# feedback/tasks.py
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid

from celery import shared_task

from rmc_rest_api.settings import EMAIL_HOST_USER, EMAIL_PORT, EMAIL_HOST_PASSWORD, EMAIL_HOST

logger = logging.getLogger('feedback')


def _send(to: str, subject: str, body: str) -> None:
    msg = MIMEMultipart()
    msg["From"] = f"RMC <{EMAIL_HOST_USER}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="krasrm.com")
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # ИСПРАВЛЕНО: используем EMAIL_HOST, а не EMAIL_HOST_USER
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        s.sendmail(EMAIL_HOST_USER, to, msg.as_string())

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_feedback_email(self, name: str, phone: str, email: str, message: str, created: str) -> str:
    """Отправка уведомления админу"""
    logger.info(f"[TASK ADMIN] Sending to {EMAIL_HOST_USER}")
    try:
        _send(
            to=EMAIL_HOST_USER,
            subject="Новое обращение с сайта",
            body=(
                f"Получено новое обращение:\n\n"
                f"Имя:     {name}\n"
                f"Телефон: {phone}\n"
                f"Почта:   {email}\n"
                f"Дата:    {created}\n\n"
                f"Сообщение:\n{message}"
            ),
        )
        logger.info(f"[TASK ADMIN] ✅ Sent")
        return f"Admin notification sent"
    except Exception as e:
        logger.error(f"[TASK ADMIN] ❌ Failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_feedback_mail(self, name: str, email: str, message: str, created: str) -> str:
    """Отправка подтверждения пользователю"""
    logger.info(f"[TASK USER] Sending to {email}")
    try:
        _send(
            to=email,
            subject="Мы получили ваше обращение",
            body=(
                f"Здравствуйте, {name}!\n\n"
                f"Ваше обращение принято. Мы свяжемся с вами в ближайшее время.\n\n"
                f"Текст вашего сообщения:\n{message}"
            ),
        )
        logger.info(f"[TASK USER] ✅ Sent")
        return f"Письмо отправлено для {email}"
    except Exception as e:
        logger.error(f"[TASK USER] ❌ Failed: {e}")
        raise self.retry(exc=e)