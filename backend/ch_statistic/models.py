"""
Модели для статистики в ClickHouse.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Убрано дублирующее поле played_krasnoyarsk
2. Время хранится в UTC, конвертация в локальное время происходит при выводе
"""

from django.db.models import F
from django.conf import settings

from clickhouse_backend import models


def statistic_engine():
    """Physical layout shared by raw statistic tables."""
    return models.MergeTree(
        order_by=("client", "played", "id"),
        partition_by=models.toYYYYMM(F("played")),
        storage_policy="statistics_tiered",
    )


def statistic_table(name):
    """Return the active physical table without changing the API contract."""
    return f"{name}{settings.CLICKHOUSE_STATISTICS_TABLE_SUFFIX}"


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
        db_table = statistic_table('ad_stat')
        engine = statistic_engine()
        verbose_name = 'Статистика рекламы'
        verbose_name_plural = 'Статистика рекламы'


class MusicStat(Stat):
    """Статистика музыки."""

    class Meta:
        db_table = statistic_table('music_stat')
        engine = statistic_engine()
        ordering = ['-played']
        verbose_name = 'Статистика музыки'
        verbose_name_plural = 'Статистика музыки'


class ImageStat(Stat):
    """Статистика фоновых картинок."""

    class Meta:
        db_table = statistic_table('image_stat')
        engine = statistic_engine()
        ordering = ['-played']
        verbose_name = 'Статистика изображений'
        verbose_name_plural = 'Статистика изображений'


class BackupImageStat(Stat):
    """Бэкап статистики фоновых картинок."""

    class Meta:
        # Legacy task compatibility. Retention is now handled by ClickHouse
        # TTL, so this table is not part of the v2 reader/writer cutover.
        db_table = 'image_stat_backup'
        engine = statistic_engine()
        ordering = ['-played']
        verbose_name = 'Бэкап статистики изображений'
        verbose_name_plural = 'Бэкапы статистики изображений'


class VideoStat(Stat):
    """Статистика фоновых видео."""

    class Meta:
        db_table = statistic_table('video_stat')
        engine = statistic_engine()
        ordering = ['-played']
        verbose_name = 'Статистика видео'
        verbose_name_plural = 'Статистика видео'


class TickerStat(Stat):
    """Статистика бегущей строки."""

    class Meta:
        db_table = statistic_table('ticker_stat')
        engine = statistic_engine()
        ordering = ['-played']
        verbose_name = 'Статистика бегущей строки'
        verbose_name_plural = 'Статистика бегущих строк'
