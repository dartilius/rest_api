from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.db import models
from uuid import uuid4
from phonenumber_field.modelfields import PhoneNumberField

from api.custom_base_user import CustomUserManager

ROLES = {
    'admin': 'Сотрудник ТО',
    'manager': 'Менеджер',
    'superuser': 'Суперпользователь'
}


class CustomUser(AbstractUser):
    """Пользователи."""

    email_validator = EmailValidator(
        message='Такая почта уже занята, либо введены запрещённые символы. '
                'Разрешены только буквы, цифры и @/./+/-/_ символы, '
                'а почта должна иметь такой вид: адрес@домен'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    username = models.CharField(
        max_length=32,
        unique=True,
        default=uuid4()
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
    )
    middle_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Отчество'
    )
    role = models.CharField(
        choices=ROLES,
        max_length=32,
        null=True,
        blank=True,
        verbose_name='Роль'
    )
    phone_number = PhoneNumberField(
        unique=True,
        verbose_name='Номер телефона'
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        validators=[email_validator],
        verbose_name='Электронная почта'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Актуальность пользователя'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    @property
    def is_manager(self):
        """Проверяем, что пользователь менеджер."""
        return self.role == 'manager'

    @property
    def is_admin(self):
        """Проверяем, что пользователь админ."""
        return self.role == 'admin'

    def save(self, *args, **kwargs):
        self.username = self.email
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'custom_user'
        ordering = ('-created',)
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'
