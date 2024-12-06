from uuid import uuid4
from django.db import transaction
from django.db.models import DO_NOTHING, ForeignKey, Model
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
        kwargs['blank'] = True
        kwargs['unique'] = True
        super(Article, self).__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = super(Article, self).check(**kwargs)
        errors.extend(self._check_key())
        return errors

    def _check_key(self):
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
        name, path, args, kwargs = super(Article, self).deconstruct()
        del kwargs['blank']
        kwargs['unique'] = True
        return name, path, args, kwargs

    def get_internal_type(self):
        return "Article"

    def to_python(self, value):
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

    def get_db_prep_save(self, value, connection):
        if value is None:
            return None
        return super(Article, self).get_db_prep_save(value, connection)

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return None
        return int(value)

    def contribute_to_class(self, cls, name, **kwargs):
        assert not cls._meta.auto_field, "Может быть только одно auto-поле."
        super(Article, self).contribute_to_class(cls, name, **kwargs)
        cls._meta.auto_field = self

    def pre_save(self, model_instance, add):
        # Проверяем, что значение корректно встало
        value = getattr(model_instance, self.attname, None)
        if value is None and add:
            value = self.get_next_value(model_instance)
            setattr(model_instance, self.attname, value)
        return value

    def get_next_value(self, model_instance):
        with transaction.atomic():
            # Лочим табличку чтобы избежать race conditions
            last_instance = model_instance.__class__.objects.select_for_update(
            ).order_by('-' + self.attname).first()
            if last_instance:
                return getattr(last_instance, self.attname) + 1
            return 1

    def formfield(self, **kwargs):
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

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
