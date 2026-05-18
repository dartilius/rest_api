from re import match
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction
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

from api.custom_managers import InactiveManager, ForWebManager

TYPE_OF_CONTACT = [
    ("CA", "Контактное лицо контрагента"),
    ("LK", "Личный контакт"),
    ("other", "Прочие"),
]

GENDER = [
    ("man", "Мужской"),
    ("women", "Женский"),
    ("tab", "Табуретка"),
]

CONTACTINFO = [
    ("address", "Адрес"),
    ("phone", "Телефон"),
    ("mail", "Адрес электронной почты"),
    ("web", "Веб-страница"),
    ("messenger", "Мессенджер"),
    ("other", "Другое"),
]

TYPEOFPHONE = [
    ("mobkl", "Телефон мобильный КЛ"),
    ("dop", "Дополнительный"),
    ("mobkldop", "Телефон дополнительный КЛ"),
]

TYPEMAIL = [
    ("rab", "E-mail рабочий КЛ"),
    ("dop", "E-mail дополнительный КЛ"),
    ("lich", "E-mail личный"),
]


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


class FirstName(Model):
    first_name = CharField()
    class Meta:
        abstract = True


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

    id = UUIDPKField()
    owner = ForeignKey(
        "users.CustomUser",
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
    inactive = InactiveManager()
    objects = Manager()
    web = ForWebManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ContactInformation(Model):
    """Контактная информация (телефон, почта, адрес и т.д.)."""
    basic = BooleanField(default=False, verbose_name="Основной")
    type = CharField(max_length=255, choices=CONTACTINFO, null=True, blank=True)

    vidtel = CharField(max_length=255, null=True, blank=True, choices=TYPEOFPHONE, verbose_name="Вид телефона")
    vidmail = CharField(max_length=255, null=True, blank=True, choices=TYPEMAIL, verbose_name="Вид почты")

    meaning = CharField(max_length=255, null=True, blank=True)
    ext = CharField(max_length=255, null=True, blank=True, verbose_name="Доб.")
    comment = CharField(max_length=255, null=True, blank=True, verbose_name="Комментарий")

    class Meta:
        abstract = True
        verbose_name = "Контактная информация"
        verbose_name_plural = "Контактная информация"

    def __str__(self):
        return f"{self.type}: {self.meaning}"

    def clean(self):
        if not self.type:
            return
        """Валидация значений в зависимости от типа."""
        if self.type == "phone":
            if not match(r"^\+?[0-9\-\(\) ]+$", self.meaning or ""):
                raise ValidationError("Значение должно быть корректным номером телефона.")
            if not self.vidtel:
                raise ValidationError("Для типа 'Телефон' нужно указать вид телефона.")
            self.vidmail = None
        elif self.type == "mail":
            if not match(r"^[\w\.-]+@[\w\.-]+\.\w+$", self.meaning or ""):
                raise ValidationError("Значение должно быть корректным адресом электронной почты.")
            if not self.vidmail:
                raise ValidationError("Для типа 'Почта' нужно указать вид почты.")
            self.vidtel = None
        else:
            self.vidtel = None
            self.vidmail = None