from clickhouse_backend import models


class Stat(models.ClickhouseModel):
    """Базовая статистика."""

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Запись создана'
    )
    played = models.DateTimeField(
        verbose_name='Когда было проиграно'
    )
    file = models.StringField(
        max_length=36,
        verbose_name='Идентификатор файла'
    )
    client = models.StringField(
        max_length=36,
        verbose_name='Идентификатор номенклатуры'
    )
    length = models.UInt16Field(
        verbose_name='Хронометраж'
    )

    class Meta:
        abstract = True
        ordering = ('-created',)

    def __str__(self):
        return self.file


class ADStat(Stat):
    """Статистика рекламы."""

    ad_block = models.UInt32Field(verbose_name='Рекламный блок')

    class Meta:
        db_table = 'ad_stat'
        verbose_name = 'Статистика рекламы'
        verbose_name_plural = 'Статистика рекламы'


class MusicStat(Stat):
    """Статистика музыки."""

    class Meta:
        db_table = 'music_stat'
        ordering = ['-played']
        verbose_name = 'Статистика музыки'
        verbose_name_plural = 'Статистика музыки'


class ImageStat(Stat):
    """Статистика фоновых картинок."""

    class Meta:
        db_table = 'image_stat'
        ordering = ['-played']
        verbose_name = 'Статистика изображений'
        verbose_name_plural = 'Статистика изображений'


class VideoStat(Stat):
    """Статистика фоновых видео."""

    class Meta:
        db_table = 'video_stat'
        ordering = ['-played']
        verbose_name = 'Статистика видео'
        verbose_name_plural = 'Статистика видео'


class TickerStat(Stat):
    """Статистика бегущей строки."""

    class Meta:
        db_table = 'ticker_stat'
        ordering = ['-played']
        verbose_name = 'Статистика бегущей строки'
        verbose_name_plural = 'Статистика бегущих строк'
