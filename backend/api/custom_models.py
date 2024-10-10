from uuid import uuid4
from django.db import models


class UUIDPKField(models.UUIDField):

    def __init__(self,
                 primary_key=True,
                 default=uuid4,
                 editable=False,
                 verbose_name='Уникальный идентификатор',
                 *args,
                 **kwargs):
        self.primary_key = primary_key
        self.default = default
        self.editable = editable
        self.verbose_name = verbose_name
        super().__init__(*args, **kwargs)


class APIBaseModel(models.Model):

    from users.models import CustomUser

    id = UUIDPKField()
    owner = models.ForeignKey(
        CustomUser,
        related_name='%(class.Meta.db_table)s',
        verbose_name='Создатель',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Наименование',
        unique=True
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_active = False
