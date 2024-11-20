from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import EmailValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from api.custom_user import CustomUserManager

ROLES = {
    'admin': 'Сотрудник ТО',
    'manager': 'Менеджер',
    'ordinary': 'Пользователь',
    'superuser': 'Суперпользователь'
}


class CustomUser(AbstractBaseUser, PermissionsMixin):
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
        blank=True
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
    def full_name(self):
        return {
            'full_name': f'{self.last_name} {self.first_name}'
        }

    def save(self, *args, **kwargs):
        self.username = self.email
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'custom_user'
        ordering = ('-created',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.full_name['full_name']
