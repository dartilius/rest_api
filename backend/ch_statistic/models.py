from clickhouse_backend import models

from nomenclatures.models import Nomenclature


class Stat(models.ClickhouseModel):
    """Базовая статистика."""

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Запись создана'
    )
    played = models.DateTimeField(
        verbose_name='Когда было проиграно'
    )
    value = models.StringField(
        max_length=288,
        verbose_name='Контрольная сумма'
    )
    client = models.StringField(
        max_length=288,
        verbose_name='Номенклатура'
    )
    length = models.UInt16Field(
        verbose_name='Хронометраж'
    )

    class Meta:
        abstract = True
        ordering = ('-created',)


class ADStat(Stat):
    """Статистика рекламы."""

    ad_block = models.UInt32Field()

    class Meta:
        db_table = 'ad_stat'
        verbose_name = 'Статистика рекламы'
        verbose_name_plural = 'Статистика рекламы'

    def __str__(self):
        return self.value


class MusicStat(Stat):
    """Статистика музыки."""

    class Meta:
        db_table = 'music_stat'
        verbose_name = 'Статистика музыки'
        verbose_name_plural = 'Статистика музыки'

    def __str__(self):
        return self.value


class ImageStat(Stat):
    """Статистика фоновых картинок."""

    class Meta:
        db_table = 'image_stat'
        verbose_name = 'Статистика изображений'
        verbose_name_plural = 'Статистика изображений'

    def __str__(self):
        return self.value


class VideoStat(Stat):
    """Статистика фоновых видео."""

    class Meta:
        db_table = 'video_stat'
        verbose_name = 'Статистика видео'
        verbose_name_plural = 'Статистика видео'

    def __str__(self):
        return self.value


class TickerStat(Stat):
    """Статистика бегущей строки."""

    class Meta:
        db_table = 'ticker_stat'
        verbose_name = 'Статистика бегущей строки'
        verbose_name_plural = 'Статистика бегущих строк'

    def __str__(self):
        return self.value
