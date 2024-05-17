# from uuid import uuid4

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

# from nomenclatures.models import Nomenclature

ROLES = {
    'admin': 'Сотрудник ТО',
    'manager': 'Менеджер',
    'superuser': 'Суперпользователь'
}


class CustomUser(AbstractUser):
    """Пользователи."""

    username_validator = UnicodeUsernameValidator(
        message='Такой юзернейм уже занят либо введены запрещённые символы.'
                'Разрешены только буквы, цифры и @/./+/-/_ символы.'
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
        verbose_name='Логин',
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
        verbose_name='Роль',
        null=True,
        blank=True
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        verbose_name='Электронная почта'
    )
    phone_number = PhoneNumberField(
        unique=True,
        verbose_name='Номер телефона'
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

    class Meta:
        db_table = 'custom_user'
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


# class RMPIUser(AbstractUser):
#     """Пользователи разбы."""
#
#     id = models.ForeignKey(
#         Nomenclature,
#         related_name="rmpi",
#         primary_key=True,
#         on_delete=models.CASCADE
#     )
#     username = models.UUIDField(
#         max_length=36,
#         default=uuid4,
#         editable=False,
#         verbose_name="Логин"
#     )
