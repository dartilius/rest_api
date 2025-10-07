from clickhouse_backend import models
from django.utils.translation import gettext_lazy as _


class Stat(models.ClickhouseModel):
    """
    Абстрактная базовая модель статистики.
    
    Attributes:
        created (DateTime): Дата создания записи
        played (DateTime): Дата и время проигрывания
        file (String): UUID файла (36 символов)
        client (String): UUID номенклатуры (36 символов)
        length (UInt16): Длительность в секундах
    """

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Запись создана')
    )
    played = models.DateTimeField(
        verbose_name=_('Когда было проиграно')
    )
    file = models.StringField(
        max_length=36,
        verbose_name=_('Идентификатор файла')
    )
    client = models.StringField(
        max_length=36,
        verbose_name=_('Идентификатор номенклатуры')
    )
    length = models.UInt16Field(
        verbose_name=_('Хронометраж (секунды)')
    )

    class Meta:
        abstract = True
        ordering = ('-created',)
        # Убраны индексы для ClickHouse, так как они создаются автоматически
        # или требуют специального синтаксиса для ClickHouse Backend

    def __str__(self):
        return f"{self.file} - {self.played}"


class ADStat(Stat):
    """
    Статистика рекламы с дополнительным полем рекламного блока.
    
    Attributes:
        ad_block (UInt32): Длительность рекламного блока в секундах
    """

    ad_block = models.UInt32Field(verbose_name=_('Рекламный блок (секунды)'))

    class Meta:
        db_table = 'ad_stat'
        verbose_name = _('Статистика рекламы')
        verbose_name_plural = _('Статистика рекламы')
        ordering = ['-played']


class MusicStat(Stat):
    """Статистика проигрывания музыки."""

    class Meta:
        db_table = 'music_stat'
        ordering = ['-played']
        verbose_name = _('Статистика музыки')
        verbose_name_plural = _('Статистика музыки')


class ImageStat(Stat):
    """Статистика показа фоновых изображений."""

    class Meta:
        db_table = 'image_stat'
        ordering = ['-played']
        verbose_name = _('Статистика изображений')
        verbose_name_plural = _('Статистика изображений')


class BackupImageStat(Stat):
    """
    Модель для бэкапа старой статистики изображений.
    Используется для архивирования данных старше определенного срока.
    """

    class Meta:
        db_table = 'image_stat_backup'
        ordering = ['-played']
        verbose_name = _('Бэкап статистики изображений')
        verbose_name_plural = _('Бэкапы статистики изображений')


class VideoStat(Stat):
    """Статистика проигрывания фоновых видео."""

    class Meta:
        db_table = 'video_stat'
        ordering = ['-played']
        verbose_name = _('Статистика видео')
        verbose_name_plural = _('Статистика видео')


class TickerStat(Stat):
    """Статистика показа бегущих строк."""

    class Meta:
        db_table = 'ticker_stat'
        ordering = ['-played']
        verbose_name = _('Статистика бегущей строки')
        verbose_name_plural = _('Статистика бегущих строк')
