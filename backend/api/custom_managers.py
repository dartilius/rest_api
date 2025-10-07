from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.db.models import Manager, Q


class CustomUserManager(UserManager):
    """
    Кастомный менеджер пользователей без поля username.
    
    Оптимизирован для работы только с email в качестве идентификатора.
    """
    
    def _create_user(self, email, password, **extra_fields):
        """
        Создает и сохраняет пользователя с заданным email и паролем.
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
            **extra_fields: Дополнительные поля
            
        Returns:
            User: Созданный пользователь
        """
        if not email:
            raise ValueError('Email должен быть указан')
            
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        """
        Создает обычного пользователя.
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
            **extra_fields: Дополнительные поля
            
        Returns:
            User: Созданный пользователь
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        """
        Создает суперпользователя.
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
            **extra_fields: Дополнительные поля
            
        Returns:
            User: Созданный суперпользователь
            
        Raises:
            ValueError: Если не установлены флаги is_staff или is_superuser
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superuser')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)
    
    def get_by_natural_key(self, username):
        """
        Получение пользователя по natural key (email).
        
        Args:
            username: Email пользователя
            
        Returns:
            User: Найденный пользователь
        """
        return self.get(email__iexact=username)


class ActiveManager(Manager):
    """
    Менеджер для активных объектов.
    
    Возвращает только объекты с is_active=True.
    """
    
    def get_queryset(self):
        """
        Возвращает QuerySet только с активными объектами.
        
        Returns:
            QuerySet: QuerySet с фильтром is_active=True
        """
        return super().get_queryset().filter(is_active=True)
    
    def inactive(self):
        """
        Возвращает неактивные объекты.
        
        Returns:
            QuerySet: QuerySet с фильтром is_active=False
        """
        return self.get_queryset().filter(is_active=False)
