from django.contrib.postgres.fields import DateTimeRangeField, HStoreField
from django.db import models

from nomenclatures.models import NomenclatureGroup, Nomenclature
from users.models import CustomUser
from files.models import Playlist, File

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


class BaseOrder(models.Model):
    """Заказ."""

    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Описание'
    )
    broadcast_interval = DateTimeRangeField(
        verbose_name='Интервал работы заказа'
    )
    status = models.CharField(
        choices=STATUSES,
        verbose_name='Статус',
        default=0
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    class Meta:
        abstract = True


class AdOrder(BaseOrder):
    """Рекламный заказ."""

    owner = models.ForeignKey(
        CustomUser,
        verbose_name='Создатель',
        related_name='ad_orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    group = models.ForeignKey(
        NomenclatureGroup,
        related_name='ad_orders',
        verbose_name='Группа номенклатур',
        on_delete=models.CASCADE
    )
    file = models.ForeignKey(
        File,
        verbose_name='Файл',
        related_name='ad_orders',
        on_delete=models.CASCADE
    )
    slides = models.ManyToManyField(
        File,
        verbose_name='Слайды',
        related_name='slides_orders',
        blank=True
    )
    broadcast_type = models.PositiveSmallIntegerField(
        choices=BROADCAST_TYPES,
        default=0,
        verbose_name='Тип вещания'
    )
    parameters = HStoreField(
        default=dict,
        verbose_name='Параметры заказа'
    )

    class Meta:
        db_table = 'ad_order'
        ordering = ('-created',)
        verbose_name = 'Рекламный заказ'
        verbose_name_plural = 'Реклама'


class BgOrder(BaseOrder):
    """Фоновый заказ."""

    owner = models.ForeignKey(
        CustomUser,
        verbose_name='Создатель',
        related_name='bg_orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    client = models.ForeignKey(
        Nomenclature,
        related_name='bg_orders',
        verbose_name='Номенклатура',
        on_delete=models.CASCADE
    )
    playlist = models.ForeignKey(
        Playlist,
        related_name='bg_orders',
        verbose_name='Плейлист',
        on_delete=models.CASCADE
    )
    order_type = models.IntegerField(
        choices=ORDER_TYPES,
        verbose_name='Тип фона'
    )

    class Meta:
        db_table = 'bg_order'
        ordering = ('-created',)
        verbose_name = 'Фоновый заказ'
        verbose_name_plural = 'Фон'
