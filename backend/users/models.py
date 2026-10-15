from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import EmailValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django_minio_backend import MinioBackend
from django.contrib.postgres.indexes import GinIndex
from api import ContactInformation
from api.base_objects import UUIDPKField
from api.custom_managers import CustomUserManager
from django.utils import timezone

CONTACT_PERSON_ROLES = [
    ('broadcast', 'Корп. вещание'),
    ('ad', 'Реклама'),
]

EMPLOYEE_ROLES = [
    ('admin', 'Сотрудник ТО'),
    ('manager', 'Менеджер'),
    ('superuser', 'Суперпользователь'),
]

ROLES = [
    ('ordinary', 'Пользователь'),
] + CONTACT_PERSON_ROLES + EMPLOYEE_ROLES

EMPLOYEE_ROLE_KEYS = {r[0] for r in EMPLOYEE_ROLES}
CONTACT_PERSON_ROLE_KEYS = {r[0] for r in CONTACT_PERSON_ROLES}

class ContactInfo(ContactInformation):
    id = UUIDPKField()
    user = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='contacts_cp',
        verbose_name='Пользователь'
    )
    class Meta:
        db_table = "contact_info"
        verbose_name = "Контактная информация"
        verbose_name_plural = 'Контактная информация'

class RegistrationEmailVerification(models.Model):
    """One-time email verification state used before self-registration."""

    email = models.EmailField(max_length=255, unique=True)
    code = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_consent_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        db_table = 'registration_email_verification'
        verbose_name = 'Подтверждение email при регистрации'
        verbose_name_plural = 'Подтверждения email при регистрации'
        indexes = [models.Index(fields=['expires_at'])]

    @property
    def is_verified(self):
        return self.verified_at is not None and self.expires_at > timezone.now()


class PasswordResetEmailVerification(models.Model):
    """One-time email verification state used before a password reset."""

    email = models.EmailField(max_length=255, unique=True)
    code = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'password_reset_email_verification'
        verbose_name = 'Подтверждение сброса пароля'
        verbose_name_plural = 'Подтверждения сброса пароля'
        indexes = [models.Index(fields=['expires_at'])]


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Пользователи."""

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = EMAIL_FIELD
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
    id = UUIDPKField()
    avatar = models.FileField(
        upload_to='user_avatars',
        storage=MinioBackend(bucket_name="local-media"),
        null=True,
        blank=True,
        verbose_name='Аватар пользователя'
    )

    email_validator = EmailValidator(
        message='Емэйл уже занят, либо введён некорректно. '
                'Разрешены только буквы, цифры и @/./+/-/_ символы, '
                'а почта должна иметь такой вид: адрес@домен'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        null=True,
        blank=True
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        null=True,
        blank=True
    )
    middle_name = models.CharField(
        max_length=150,
        verbose_name='Отчество',
        null=True,
        blank=True
    )
    role = models.CharField(
        choices=ROLES,
        max_length=32,
        verbose_name='Роль',
        default='ordinary'
    )
    phone_number = PhoneNumberField(
        unique=True,
        verbose_name='Номер телефона',
        null=True,
        blank=True,
        region="RU"
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        validators=[email_validator],
        verbose_name='Электронная почта',
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        verbose_name='Актуальность пользователя',
        default=True
    )
    is_staff = models.BooleanField(
        verbose_name='Пользователь админ-панели',
        help_text='Влияет на возможность зайти в админ-панель django',
        default=False
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    code1c = models.CharField(
        default='',
        blank=True,
        null=True,
        verbose_name='Код 1с'
    )

    token_1c_access = models.TextField(
        blank=True, null=True,
        verbose_name='Access-токен 1С'
    )
    token_1c_refresh = models.TextField(
        blank=True, null=True,
        verbose_name='Refresh-токен 1С'
    )

    @property
    def is_manager(self):
        """Проверяем, что пользователь менеджер."""
        return self.role == 'manager'

    @property
    def is_admin(self):
        """Проверяем, что пользователь админ."""
        return self.role == 'admin'

    @property
    def is_ordinary(self):
        """Проверяем, что это обычный пользователь."""
        return self.role == 'ordinary'

    @property
    def is_super_user(self):
        """Проверяем, что это superuser."""
        return self.role in EMPLOYEE_ROLE_KEYS

    @property
    def is_contact_person_ad(self):
        """Контактное лицо — реклама."""
        return self.role == 'ad'

    @property
    def is_contact_person_broadcast(self):
        """Контактное лицо — корп. вещание."""
        return self.role == 'broadcast'

    @property
    def is_employee(self) -> bool:
        return self.role in EMPLOYEE_ROLE_KEYS

    @property
    def is_contact_person(self) -> bool:
        return self.role in CONTACT_PERSON_ROLE_KEYS


    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()

    # def get_full_name(self):
    #     """Возвращает полное имя пользователя для админки и Django."""
    #     return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()

    def get_short_name(self):
        """Возвращает короткое имя пользователя для админки и Django."""
        return self.first_name

    def save(self, *args, **kwargs):
        self.username = self.email
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'custom_user'
        ordering = ('-created',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        indexes = [
            GinIndex(
                name="user_name_gin_idx",
                fields=["first_name", "middle_name", "last_name"],
                opclasses=["gin_trgm_ops", "gin_trgm_ops", "gin_trgm_ops"],
            ),
            models.Index(fields=['email']),
            models.Index(fields=['first_name']),
            models.Index(fields=['last_name']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['code1c']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return self.full_name


class PersonalDataConsent(models.Model):
    """No duplicate contact details; evidence follows its subject's lifetime."""

    purpose = models.CharField(max_length=20, choices=[
        ('feedback', 'Обращение'), ('registration', 'Регистрация'),
    ])
    document_version = models.CharField(max_length=50)
    document_sha256 = models.CharField(max_length=64)
    accepted_at = models.DateTimeField(default=timezone.now, editable=False)
    source = models.CharField(max_length=40, default='django-public-api', editable=False)
    subject_reference = models.CharField(max_length=64, blank=True, editable=False)
    feedback = models.OneToOneField(
        'feedback.Feedback', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='personal_data_consent',
    )
    registration = models.ForeignKey(
        RegistrationEmailVerification, null=True, blank=True,
        on_delete=models.CASCADE, related_name='consents',
    )
    user = models.ForeignKey(
        CustomUser, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='personal_data_consents',
    )
    revoked_at = models.DateTimeField(null=True, blank=True, editable=False)
    evidence_delete_after = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        permissions = [('manage_privacy', 'Обрабатывать запросы субъектов данных')]
        constraints = [
            models.UniqueConstraint(
                fields=['registration', 'purpose', 'document_version'],
                condition=models.Q(revoked_at__isnull=True),
                name='unique_active_registration_consent',
            ),
        ]


class PrivacyRequest(models.Model):
    """Staff records verification and execution without copying form/contact data."""

    kind = models.CharField(max_length=20, choices=[
        ('withdraw', 'Отзыв'), ('correct', 'Исправление'), ('delete', 'Удаление'),
    ])
    received_at = models.DateTimeField(default=timezone.now)
    identity_verified_at = models.DateTimeField(null=True, blank=True)
    identity_check_reference = models.CharField(max_length=120, blank=True)
    consent = models.ForeignKey(
        PersonalDataConsent, null=True, blank=True, on_delete=models.SET_NULL,
    )
    feedback = models.ForeignKey(
        'feedback.Feedback', null=True, blank=True, on_delete=models.SET_NULL,
    )
    user = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Получен'), ('completed', 'Исполнен'), ('retained', 'Сохранено по основанию'),
    ])
    result = models.TextField(blank=True, help_text='Результат без контактов, паролей и копий документов.')
    lawful_basis = models.TextField(blank=True)
    retention_until = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True, editable=False)
    delete_after = models.DateTimeField(null=True, blank=True)
    handled_by = models.ForeignKey(
        CustomUser, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='handled_privacy_requests', editable=False,
    )

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.status != 'pending':
            if not (self.identity_verified_at and self.identity_check_reference and self.result):
                raise ValidationError('Нужны проверка личности и результат.')
            if self.status == 'retained' and not (self.lawful_basis and self.retention_until):
                raise ValidationError('Укажите основание и срок сохранения данных.')
            if self.status == 'retained' and self.retention_until <= timezone.now():
                raise ValidationError('Срок сохранения данных должен быть в будущем.')
            if self.identity_verified_at > timezone.now():
                raise ValidationError('Дата проверки личности не может быть в будущем.')
            if self.delete_after and self.delete_after <= timezone.now():
                raise ValidationError('Срок хранения запроса должен быть в будущем.')
            if self.kind == 'withdraw' and not self.consent_id:
                raise ValidationError('Выберите конкретное согласие для отзыва.')
            if self.kind == 'delete' and self.feedback_id and self.status == 'completed':
                if self.feedback.contract_status != 'none':
                    raise ValidationError('Сначала подтвердите отсутствие договора.')
                if (self.feedback.lawful_retention_until
                        and self.feedback.lawful_retention_until > timezone.now()):
                    raise ValidationError('Действует отдельное законное основание хранения.')
        if self.consent_id:
            if self.user_id and self.consent.user_id != self.user_id:
                raise ValidationError('Согласие не принадлежит выбранному пользователю.')
            if self.feedback_id and self.consent.feedback_id != self.feedback_id:
                raise ValidationError('Согласие не относится к выбранному обращению.')


class PrivacyErasure(models.Model):
    """Non-contact tombstone for reapplying erasures after backup restoration."""

    subject_type = models.CharField(max_length=30)
    subject_id = models.CharField(max_length=64)
    erased_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['subject_type', 'subject_id'], name='unique_privacy_erasure',
        )]

