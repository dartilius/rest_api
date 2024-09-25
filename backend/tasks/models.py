from uuid import uuid4

from django.contrib.postgres.fields import HStoreField
from django.db import models
from nomenclatures.models import Nomenclature
from users.models import CustomUser

STATUSES = {
    0: 'Ожидает обработки',
    1: 'В обработке',
    2: 'Выполнена',
    3: 'Отменена',
    4: 'Ошибка'
}

TASK_TYPES = {
    # create order
    0: 'BGMUSIC',
    1: 'BGVIDEO',
    2: 'BGIMAGE',
    3: 'TICKER',
    4: 'AD',
    # cancel order
    5: 'CANCEL_BGMUSIC',
    6: 'CANCEL_BGVIDEO',
    7: 'CANCEL_BGIMAGE',
    8: 'CANCEL_TICKER',
    9: 'CANCEL_AD',
    # update order
    10: 'UPDATE_BGMUSIC',
    11: 'UPDATE_BGVIDEO',
    12: 'UPDATE_BGIMAGE',
    13: 'UPDATE_TICKER',
    14: 'UPDATE_AD',
    # not order
    15: 'REBOOT',
    16: 'UPDATE',
    17: 'CUSTOM',
    18: 'SET_PARAMETERS',
    19: 'PLACEHOLDER'
}


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
        CustomUser,
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
    type = models.PositiveSmallIntegerField(
        choices=TASK_TYPES,
        verbose_name='Тип',
        editable=False,
        default=0
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        verbose_name='Статус',
        default=0
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время создания'
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Время выполнения'
    )

    class Meta:
        db_table = 'task'
        ordering = ('-created',)
        verbose_name = 'Репликация'
        verbose_name_plural = 'Репликации'

    def __str__(self):
        return TASK_TYPES[int(self.type)]
