from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from api.base_objects import UUIDPKField
from api.custom_managers import CustomUserManager

from api.base_objects import ContactInformation

CONTACT_PERSON_ROLES = [
    ('broadcast', 'Корп. вещание'),
    ('ad', 'Реклама'),
]

ROLES = [
    ('admin', 'Сотрудник ТО'),
    ('manager', 'Менеджер'),
    ('superuser', 'Суперпользователь'),
    ('ordinary', 'Пользователь'),
] + CONTACT_PERSON_ROLES


class CustomUser(AbstractBaseUser, PermissionsMixin, ContactInformation):
    """Пользователи."""

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = EMAIL_FIELD
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    email_validator = EmailValidator(
        message='Емэйл уже занят, либо введён некорректно. '
                'Разрешены только буквы, цифры и @/./+/-/_ символы, '
                'а почта должна иметь такой вид: адрес@домен'
    )

    id = UUIDPKField()
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
        verbose_name='Электронная почта'
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

    additional_contact_info = ArrayField(
        base_field=models.JSONField(),
        default=list,
        blank=True,
        verbose_name="Доп. контактная информация"
    )
    code1c = models.CharField(
        default='',
        blank=True,
        null=True,
        verbose_name='Код 1с'
    )

    def clean(self):
        """Валидация элементов additional_contact_info через ContactInformation.clean()."""
        super().clean()

        for i, item in enumerate(self.additional_contact_info):
            fake = ContactInformation(
                basic=item.get("basic"),
                type=item.get("type"),
                vidtel=item.get("vidtel"),
                vidmail=item.get("vidmail"),
                meaning=item.get("meaning"),
                ext=item.get("ext"),
                comment=item.get("comment"),
            )
            try:
                fake.clean()
            except ValidationError as e:
                raise ValidationError({f"additional_contact_info[{i}]": e})

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
        return self.role == 'superuser'

    @property
    def is_contact_person_ad(self):
        """Контактное лицо — реклама."""
        return self.role == 'ad'

    @property
    def is_contact_person_broadcast(self):
        """Контактное лицо — корп. вещание."""
        return self.role == 'broadcast'

    @property
    def full_name(self):
        return {
            'full_name': f'{self.last_name} {self.first_name}'
        }

    def save(self, *args, **kwargs):
        self.username = self.email
        super().save(*args, **kwargs)

    def get_full_name(self):
        """Возвращает полное имя пользователя для админки и Django."""
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()

    def get_short_name(self):
        """Возвращает короткое имя пользователя для админки и Django."""
        return self.first_name

    class Meta:
        db_table = 'custom_user'
        ordering = ('-created',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.full_name['full_name']
