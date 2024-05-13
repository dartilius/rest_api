from django.contrib.postgres.fields import DateTimeRangeField, HStoreField
from django.db import models

from nomenclatures.models import NomenclatureGroup, Nomenclature
from users.models import User
from files.models import Playlist, File

ORDER_TYPES = {
    0: 'Реклама',
    1: 'Фоновая музыка',
    2: 'Фоновые видео',
    3: 'Фоновые картинки',
    4: 'Бегущая строка'
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
    broadcast_interval = DateTimeRangeField(
        verbose_name='Интервал работы заказа'
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    class Meta:
        abstract = True


class AdOrder(BaseOrder):
    """Рекламный заказ."""

    @staticmethod
    def default_parameters():
        return {
            "event": "play if click button",
            "active_ad": "close",
            "times_in_hour": 4,
            "weight": 50,
            "daily_start_time": "09:00:00",
            "daily_end_time": "21:00:00",
            "timedelta": "01:30:00"
        }

    group = models.ForeignKey(
        NomenclatureGroup,
        verbose_name='Группа номенклатур',
        on_delete=models.CASCADE
    )
    file = models.ForeignKey(
        File,
        verbose_name='Файл',
        related_name="ad_file",
        on_delete=models.CASCADE
    )
    slides = models.ManyToManyField(
        File,
        verbose_name="Слайды",
        related_name="ad_slide"
    )
    broadcast_type = models.PositiveSmallIntegerField(
        choices=BROADCAST_TYPES,
        default=0,
        verbose_name='Тип вещания'
    )
    parameters = HStoreField(
        default=default_parameters,
        verbose_name='Параметры заказа'
    )

    class Meta:
        db_table = "ad_order"
        verbose_name = "Рекламный заказ"
        verbose_name_plural = "Реклама"


class BgOrder(BaseOrder):
    """Фоновый заказ."""

    client = models.ForeignKey(
        Nomenclature,
        verbose_name='Номенклатура',
        on_delete=models.CASCADE
    )
    playlist = models.ForeignKey(
        Playlist,
        verbose_name='Плейлист',
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "bg_order"
        verbose_name = "Фоновый заказ"
        verbose_name_plural = "Фон"
