from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models

from api import APIBaseObjectModel
from nomenclatures.models import Nomenclature
from files.models import Playlist

ORDER_TYPES = {
    0: 'Фоновая музыка',
    1: 'Фоновые видео',
    2: 'Фоновые картинки',
    3: 'Бегущая строка'
}

STATUSES = {
    0: 'Ожидает эфира',
    1: 'В эфире',
    2: 'Завершён',
    3: 'Отменён',
    4: 'Ошибка'
}

BROADCAST_TYPES = {
    0: 'По времени работы точки',
    1: 'Начало работы + смещение по времени',
    2: 'Конец работы - смещение по времени',
    3: 'Конкретные часы',
    4: 'С открытия до фиксированного часа',
    5: 'С фиксированного часа до закрытия',
    6: 'Старт по событию'
}


class BaseOrder(APIBaseObjectModel):
    """Заказ."""

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Описание'
    )
    broadcast_interval = DateTimeRangeField(
        verbose_name='Интервал работы заказа'
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        verbose_name='Статус',
        default=0
    )
    client = models.ForeignKey(
        Nomenclature,
        related_name='%(class)ss',
        verbose_name='Рабочая станция',
        on_delete=models.DO_NOTHING
    )
    playlist = models.ForeignKey(
        Playlist,
        related_name='%(class)ss',
        verbose_name='Плейлист',
        on_delete=models.DO_NOTHING
    )
    parameters = models.JSONField(
        verbose_name='Параметры заказа'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class AdOrder(BaseOrder):
    """Рекламный заказ."""

    slides = models.JSONField(
        verbose_name='Слайды',
        null=True,
        blank=True
    )
    broadcast_type = models.PositiveSmallIntegerField(
        choices=BROADCAST_TYPES,
        verbose_name='Тип вещания',
        default=0
    )
    parameters = models.JSONField(
        verbose_name='Параметры заказа'
    )

    class Meta:
        db_table = 'adorder'
        ordering = ('-created',)
        verbose_name = 'Рекламный заказ'
        verbose_name_plural = 'Рекламные заказы'


class BgOrder(BaseOrder):
    """Фоновый заказ."""

    order_type = models.PositiveSmallIntegerField(
        choices=ORDER_TYPES,
        verbose_name='Тип фона'
    )
    parameters = models.JSONField(
        verbose_name='Параметры заказа',
        default=dict
    )

    class Meta:
        db_table = 'bgorder'
        ordering = ('-created',)
        verbose_name = 'Фоновый заказ'
        verbose_name_plural = 'Фоновые заказы'
