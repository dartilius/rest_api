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
        verbose_name='Описание'
    )
    type = models.PositiveSmallIntegerField(
        choices=ORDER_TYPES,
        verbose_name='Тип'
    )
    broadcast_interval = DateTimeRangeField(
        verbose_name='Интервал работы заказа'
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
