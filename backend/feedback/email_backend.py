# feedback/email_backend.py
import ssl
import logging
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.core.mail.message import sanitize_address
from smtplib import SMTP, SMTP_SSL

logger = logging.getLogger('feedback.email')


class CustomEmailBackend(SMTPBackend):
    """
    Email backend с отключенной проверкой SSL для локальной сети.
    Подходит для внутренних SMTP серверов с самоподписанными сертификатами.
    """

    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, **kwargs):

        # Создаем небезопасный SSL контекст
        self.ssl_context = ssl._create_unverified_context()

        logger.info(f"CustomEmailBackend initialized: host={host}, port={port}, "
                    f"use_tls={use_tls}, use_ssl={use_ssl}")

        super().__init__(
            host=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
            fail_silently=fail_silently,
            use_ssl=use_ssl,
            timeout=timeout,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            **kwargs
        )

    def open(self):
        """Переопределяем метод open для использования нашего SSL контекста"""
        if self.connection:
            return False

        try:
            # Используем наш небезопасный SSL контекст
            if self.use_ssl:
                self.connection = SMTP_SSL(
                    self.host,
                    self.port,
                    timeout=self.timeout,
                    context=self.ssl_context  # ← Наш контекст
                )
            else:
                self.connection = SMTP(
                    self.host,
                    self.port,
                    timeout=self.timeout
                )
                if self.use_tls:
                    self.connection.starttls(context=self.ssl_context)  # ← Наш контекст

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            logger.info(f"SMTP connection established: {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to SMTP: {e}")
            if not self.fail_silently:
                raise
            return False

    def send_messages(self, email_messages):
        """Расширенная отправка с логированием"""
        if not email_messages:
            return 0

        logger.info(f"Attempting to send {len(email_messages)} emails")

        try:
            result = super().send_messages(email_messages)
            logger.info(f"Successfully sent {result} emails")
            return result
        except Exception as e:
            logger.error(f"Failed to send emails: {e}")
            if not self.fail_silently:
                raise
            return 0