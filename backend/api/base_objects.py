from uuid import uuid4
from django.db import models


class UUIDPKField(models.UUIDField):
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


class APIBaseObjectModel(models.Model):
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
    owner = models.ForeignKey(
        CustomUser,
        related_name='%(class)ss',
        verbose_name='Создатель',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Название',
        unique=True if '%(class)s'.lower() == 'nomenclature' else False
    )
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
