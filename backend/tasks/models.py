from uuid import uuid4

from django.contrib.postgres.fields import HStoreField
from django.db import models
from nomenclatures.models import Nomenclature
from orders.models import ORDER_TYPES
from users.models import User

STATUSES = [
    (0, 'Ожидает обработки'),
    (1, 'В обработке'),
    (2, 'Выполнена'),
    (3, 'Отменена'),
    (4, 'Ошибка')
]


class Type(models.Model):
    """Тип репликации."""

    name = models.CharField(
        max_length=255,
        verbose_name='Наименование'
    )
    order_type = models.CharField(
        choices=ORDER_TYPES,
        blank=True,
        null=True,
        unique=True,
        verbose_name='Тип заказа'
    )


class Task(models.Model):
    """Репликация."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name='Уникальный идентификатор'
    )
    client = models.ForeignKey(
        Nomenclature,
        related_name='tasks',
        on_delete=models.CASCADE,
        verbose_name='Целевая рабочая станция'
    )
    owner = models.ForeignKey(
        User,
        related_name='tasks',
        verbose_name='Кто создал',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    parameters = HStoreField(
        blank=True,
        null=True,
        verbose_name='Параметры'
    )
    type = models.ForeignKey(
        Type,
        related_name='tasks',
        verbose_name='Тип',
        on_delete=models.CASCADE
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        default=0,
        verbose_name='Статус'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время создания'
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Время выполнения'
    )
