from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from users.models import PasswordResetEmailVerification, RegistrationEmailVerification


REGISTRATION_CODE_TTL = timedelta(
    minutes=getattr(settings, 'REGISTRATION_EMAIL_CODE_TTL_MINUTES', 10)
)


def send_registration_verification_code(email: str) -> None:
    """Create a new one-time code and deliver it using Django's configured mail backend."""
    code = f'{secrets.randbelow(1_000_000):06d}'
    expires_at = timezone.now() + REGISTRATION_CODE_TTL

    with transaction.atomic():
        verification, created = RegistrationEmailVerification.objects.select_for_update().get_or_create(
            email=email,
            defaults={'code': make_password(code), 'expires_at': expires_at},
        )
        if not created:
            verification.code = make_password(code)
            verification.expires_at = expires_at
            verification.verified_at = None
            verification.save(update_fields=['code', 'expires_at', 'verified_at', 'updated_at'])

    send_mail(
        subject='Код подтверждения регистрации',
        message=(f'Ваш код подтверждения регистрации: {code}.\n'
                 f'Код действует {int(REGISTRATION_CODE_TTL.total_seconds() // 60)} минут.'),
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


def confirm_registration_verification_code(email: str, code: str) -> bool:
    """Mark a non-expired code as verified. Codes are stored only as password hashes."""
    with transaction.atomic():
        verification = (RegistrationEmailVerification.objects.select_for_update()
                        .filter(email=email, expires_at__gt=timezone.now()).first())
        if verification is None or not check_password(code, verification.code):
            return False

        verification.verified_at = timezone.now()
        verification.save(update_fields=['verified_at', 'updated_at'])
        return True


def send_password_reset_verification_code(email: str) -> None:
    """Issue a one-time password-reset code to the user and the audit mailbox."""
    code = f'{secrets.randbelow(1_000_000):06d}'
    expires_at = timezone.now() + REGISTRATION_CODE_TTL

    with transaction.atomic():
        verification, created = PasswordResetEmailVerification.objects.select_for_update().get_or_create(
            email=email,
            defaults={'code': make_password(code), 'expires_at': expires_at},
        )
        if not created:
            verification.code = make_password(code)
            verification.expires_at = expires_at
            verification.save(update_fields=['code', 'expires_at', 'updated_at'])

    audit_email = getattr(settings, 'PASSWORD_RESET_CODE_AUDIT_EMAIL', 'info@krasrm.com')
    send_mail(
        subject='Код подтверждения сброса пароля',
        message=(f'Код подтверждения сброса пароля: {code}.\n'
                 f'Код действует {int(REGISTRATION_CODE_TTL.total_seconds() // 60)} минут.\n\n'
                 'Не сообщайте этот код никому. Если вы не запрашивали сброс пароля, '
                 'ничего не делайте и свяжитесь с вашим менеджером.'),
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )

    if audit_email and audit_email.lower() != email.lower():
        send_mail(
            subject='Запрошен сброс пароля',
            message=(f'Запрошен сброс пароля для пользователя: {email}.\n'
                     f'Код подтверждения: {code}.\n'
                     f'Код действует {int(REGISTRATION_CODE_TTL.total_seconds() // 60)} минут.'),
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[audit_email],
            fail_silently=False,
        )


def consume_password_reset_verification_code(email: str, code: str) -> bool:
    """Validate and consume a non-expired password-reset code exactly once."""
    with transaction.atomic():
        verification = (PasswordResetEmailVerification.objects.select_for_update()
                        .filter(email=email, expires_at__gt=timezone.now()).first())
        if verification is None or not check_password(code, verification.code):
            return False
        verification.delete()
        return True
