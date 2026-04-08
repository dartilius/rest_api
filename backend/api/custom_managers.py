from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.db.models import Manager


class CustomUserManager(UserManager):
    """Без поля username."""

    def _create_user(self, email, password, **extra_fields):
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superuser')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class ForWebManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(for_web=True)

class ActiveManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class InactiveManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=False)