from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models

from nomenclatures.models import NomenclatureGroup
from users.models import User
from files.models import Playlist

ORDER_TYPES = [
    (0, 'Реклама'),
    (1, 'Фоновая музыка'),
    (2, 'Фоновые видео'),
    (3, 'Фоновые картинки'),
    (4, 'Бегущая строка')
]

BROADCAST_TYPES = [
    (0, 'По времени работы точки'),
    (1, 'Начало работы + смещение по времени'),
    (2, 'Конец работы - смещение по времени'),
    (3, 'Конкретные часы'),
    (4, 'С открытия до фиксированного часа'),
    (5, 'С фиксированного часа до закрытия'),
    (6, 'Старт по событию')
]


class Order(models.Model):
    """Заказ."""

    group = models.ForeignKey(
        NomenclatureGroup,
        verbose_name='Группа номенклатур',
        on_delete=models.CASCADE
    )
    owner = models.ForeignKey(
        User,
        verbose_name='Создатель',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Описание'
    )
    type = models.PositiveSmallIntegerField(
        choices=ORDER_TYPES,
        verbose_name='Тип'
    )
    broadcast_interval = DateTimeRangeField(
        verbose_name='Интервал работы заказа'
    )
    broadcast_type = models.PositiveSmallIntegerField(
        choices=BROADCAST_TYPES,
        verbose_name='Тип вещания'
    )
    parameters = models.JSONField(
        verbose_name='Параметры заказа'
    )

    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    playlist = models.ForeignKey(
        Playlist,
        verbose_name='Плейлист',
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = 'order'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return self.name
