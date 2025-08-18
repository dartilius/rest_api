from uuid import uuid4
from django.db import transaction
from django.db.models import SET_NULL, ForeignKey, Model, Manager
from django.db.models.fields import (
    BooleanField,
    CharField,
    DateTimeField,
    IntegerField,
    UUIDField,
    BigIntegerField,
)
from django.core import checks, exceptions
from django.utils.translation import gettext_lazy as _


class UUIDPKField(UUIDField):
    """
    UUID Primary Key поле.

    :ivar primary_key: True
    :ivar default: uuid4
    :ivar editable: False
    :ivar verbose_name: 'Уникальный идентификатор'
    """

    def __init__(self, *args, **kwargs):
        kwargs['primary_key'] = True
        kwargs['default'] = uuid4
        kwargs['editable'] = False
        kwargs['verbose_name'] = 'Уникальный идентификатор'
        super().__init__(*args, **kwargs)


class Article(IntegerField):
    """
    Авто-инкрементное не-PK поле для PostgreSQL.
    Сочетает функциональность IntegerField с авто-генерацией значений.
    """
    description = _("Auto-incrementing integer field")
    empty_strings_allowed = False

    default_error_messages = {
        'invalid': _("'%(value)s' value must be an integer."),
        'negative': _("Article number cannot be negative."),
    }

    def __init__(self, *args, **kwargs):
        # Обязательные параметры для авто-инкрементного поля
        kwargs.setdefault('blank', True)
        kwargs.setdefault('unique', True)
        kwargs.setdefault('editable', False)
        kwargs.setdefault('null', True)
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        """Добавляем кастомные проверки к стандартным"""
        errors = super().check(**kwargs)
        errors.extend(self._check_key())
        return errors

    def _check_key(self):
        """Гарантируем что поле всегда unique"""
        if not self.unique:
            return [
                checks.Error(
                    "Article field must be unique.",
                    obj=self,
                    id='articles.E001',
                )
            ]
        return []

    def deconstruct(self):
        """Сериализация для миграций с сохранением критичных параметров"""
        name, path, args, kwargs = super().deconstruct()
        kwargs.update({
            'unique': True,
            'editable': False,
            'blank': True,
        })
        return name, path, args, kwargs

    def get_internal_type(self):
        """Указываем базовый тип для Django"""
        return 'IntegerField'

    def db_type(self, connection):
        """Определяем тип поля для разных СУБД"""
        if connection.vendor == 'postgresql':
            return 'serial'
        return super().db_type(connection)

    def validate(self, value, model_instance):
        """Дополнительная валидация значений"""
        super().validate(value, model_instance)
        if value is not None and value < 0:
            raise exceptions.ValidationError(
                self.error_messages['negative'],
                code='negative',
            )

    def contribute_to_class(self, cls, name, **kwargs):
        """Регистрация поля в модели с проверкой уникальности"""
        if cls._meta.auto_field:
            raise ValueError("Model can have only one auto field.")
        super().contribute_to_class(cls, name, **kwargs)

    def pre_save(self, model_instance, add):
        """Генерация нового значения перед сохранением"""
        value = getattr(model_instance, self.attname, None)
        if value is None and add:
            return self.get_next_value(model_instance.__class__)
        return value

    def get_next_value(self, model_class):
        """Безопасное получение следующего значения"""
        with transaction.atomic():
            last = model_class.objects.select_for_update() \
                .order_by('-' + self.attname) \
                .values_list(self.attname, flat=True) \
                .first()
            return (last or 0) + 1

    def formfield(self, **kwargs):
        """Отключаем поле в формах"""
        return None


class APIBaseObjectModel(Model):
    """
    Базовая модель объекта.

    Ниже перечисленны установленные по-умолчанию поля.

    :ivar id: :class:`UUIDPKField`
    :ivar owner: ``ForeignKey``
    :ivar name: ``CharField``
    :ivar is_active: ``BooleanField``
    :ivar created: ``DateTimeField``
    """

    from api.custom_managers import ActiveManager
    from users.models import CustomUser

    id = UUIDPKField()
    owner = ForeignKey(
        CustomUser,
        related_name='%(class)ss',
        verbose_name='Создатель',
        on_delete=SET_NULL,
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

    def __str__(self):
        return self.name
