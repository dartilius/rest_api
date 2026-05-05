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
    token_1c_access_expires_at = models.DateTimeField(
        blank=True, null=True,
        verbose_name='Срок жизни access-токена 1С'
    )
    token_1c_refresh_expires_at = models.DateTimeField(
        blank=True, null=True,
        verbose_name='Срок жизни refresh-токена 1С'
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

    @property
    def token_1c_access_is_expired(self) -> bool:
        if not self.token_1c_access_expires_at:
            return True
        return timezone.now() >= self.token_1c_access_expires_at

    @property
    def token_1c_refresh_is_expired(self) -> bool:
        if not self.token_1c_refresh_expires_at:
            return False  # если срок не задан — считаем бессрочным
        return timezone.now() >= self.token_1c_refresh_expires_at

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

