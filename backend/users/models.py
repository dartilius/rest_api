from uuid import uuid4

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.nomenclatures.models import Nomenclature

ROLES = [
    ("admin", "Сотрудник ТО"),
    ("manager", "Менеджер"),
    ("rmpi", "Рабочая станция"),
    ("superuser", "Суперпользователь"),
    ("auth", "Аутентифицированный пользователь")
]


class User(AbstractUser):
    """Пользователи."""

    username_validator = UnicodeUsernameValidator

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
        verbose_name="Логин"
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name="Фамилия"
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name="Имя"
    )
    middle_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Отчество"
    )
    role = models.CharField(
        choices=ROLES,
        max_length=32,
        verbose_name="Роль"
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        verbose_name="Электронная почта"
    )
    phone_number = models.CharField(
        max_length=16,  # +7(908)023-99-57
        unique=True,
        verbose_name="Номер телефона"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Актуальность пользователя"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )


class RMPIUser(AbstractUser):
    """Разбы."""

    id = models.ForeignKey(
        Nomenclature,
        related_name="rmpi",
        primary_key=True,
        on_delete=models.CASCADE
    )
    username = models.UUIDField(
        max_length=36,
        default=uuid4,
        editable=False,
        verbose_name="Логин"
    )
