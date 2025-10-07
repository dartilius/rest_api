from uuid import uuid4
from django.db import transaction
from django.db import models
from django.db.models import DO_NOTHING, ForeignKey, Model, Manager
from django.db.models.fields import (
    BooleanField,
    CharField,
    DateTimeField,
    Field,
    UUIDField,
)
from django.core import checks, exceptions
from django.utils.translation import gettext_lazy as _


class UUIDPKField(UUIDField):
    """
    UUID Primary Key поле.

    Attributes:
        primary_key: True
        default: uuid4
        editable: False
        verbose_name: 'Уникальный идентификатор'
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('primary_key', True)
        kwargs.setdefault('default', uuid4)
        kwargs.setdefault('editable', False)
        kwargs.setdefault('verbose_name', 'Уникальный идентификатор')
        super().__init__(*args, **kwargs)


class Article(Field):
    """
    Авто-инкрементное поле, но при этом не PK.

    Собрано из стандартных AutoField и IntegerField.
    """
    description = _("Integer")

    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _("'%(value)s' value must be an integer."),
    }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)
        kwargs.setdefault('unique', True)
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        """Проверяет корректность конфигурации поля."""
        errors = super().check(**kwargs)
        errors.extend(self._check_key())
        return errors

    def _check_key(self):
        """Проверяет, что поле имеет unique=True."""
        if not self.unique:
            return [
                checks.Error(
                    'Article must set key (unique=True).',
                    obj=self,
                    id='fields.E100',
                ),
            ]
        return []

    def deconstruct(self):
        """Деструктуризация для миграций."""
        name, path, args, kwargs = super().deconstruct()
        del kwargs['blank']
        kwargs['unique'] = True
        return name, path, args, kwargs

    def get_internal_type(self):
        return "Article"

    def to_python(self, value):
        """Преобразует значение в Python объект."""
        if value is None:
            return value
        try:
            return int(value)
        except (TypeError, ValueError):
            raise exceptions.ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            )

    def db_type(self, connection):
        return 'serial'

    def get_db_prep_value(self, value, connection, prepared=False):
        """Подготовка значения для базы данных."""
        if value is None:
            return None
        return int(value)

    def contribute_to_class(self, cls, name, **kwargs):
        """Добавляет поле к классу модели."""
        if cls._meta.auto_field:
            raise ValueError("Может быть только одно auto-поле.")
        super().contribute_to_class(cls, name, **kwargs)
        cls._meta.auto_field = self

    def pre_save(self, model_instance, add):
        """
        Генерирует значение перед сохранением.
        
        Args:
            model_instance: Экземпляр модели
            add: Флаг создания нового объекта
            
        Returns:
            Значение для сохранения
        """
        if not add:
            # Для существующих объектов не генерируем новое значение
            return getattr(model_instance, self.attname)
            
        value = getattr(model_instance, self.attname, None)
        if value is None:
            value = self.get_next_value(model_instance)
            setattr(model_instance, self.attname, value)
        return value

    def get_next_value(self, model_instance):
        """
        Получает следующее значение для поля.
        
        Args:
            model_instance: Экземпляр модели для определения класса
            
        Returns:
            int: Следующее значение
        """
        with transaction.atomic():
            # Лочим табличку чтобы избежать race conditions
            last_instance = model_instance.__class__.objects.select_for_update(
            ).order_by('-' + self.attname).first()
            if last_instance:
                return getattr(last_instance, self.attname) + 1
            return 1

    def formfield(self, **kwargs):
        """Не показывает поле в формах."""
        return None


class APIBaseObjectModel(Model):
    """
    Базовая модель объекта API.

    Стандартные поля:
    - id: UUIDPKField - уникальный идентификатор
    - owner: ForeignKey - создатель объекта
    - name: CharField - название объекта
    - is_active: BooleanField - флаг актуальности
    - created: DateTimeField - дата создания
    """
    
    # Импорты внутри класса для избежания circular imports
    from api.custom_managers import ActiveManager
    from users.models import CustomUser

    id = UUIDPKField()
    owner = ForeignKey(
        CustomUser,
        related_name='%(class)ss',
        verbose_name='Создатель',
        on_delete=DO_NOTHING,
        null=True,
        blank=True
    )
    name = CharField(
        max_length=255,
        verbose_name='Название'
    )
    is_active = BooleanField(
        default=True,
        verbose_name='Актуальность'
    )
    created = DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    active = ActiveManager()
    objects = Manager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_active', 'created']),
            models.Index(fields=['owner', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Сохранение объекта с предварительной проверкой.
        
        Args:
            *args: Аргументы
            **kwargs: Ключевые аргументы
            
        Raises:
            ValueError: Если название пустое
        """
        # Предварительная валидация для избежания ненужных запросов
        if not self.name or not self.name.strip():
            raise ValueError("Название не может быть пустым")
        super().save(*args, **kwargs)
