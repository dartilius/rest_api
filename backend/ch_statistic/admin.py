from django.contrib import admin

from ch_statistic.models import (
    ADStat,
    MusicStat,
    VideoStat,
    ImageStat,
    TickerStat
)

DISPLAY_LIST = (
    'client',
    'file',
    'played',
    'created',
    'length'
)

SEARCH_LIST = (
    'client',
    'file'
)

FILTER_LIST = (
    'client',
    'file'
)


@admin.register(ADStat)
class AdStatAdmin(admin.ModelAdmin):
    """Статистики рекламы."""

    list_display = DISPLAY_LIST + ('ad_block',)
    search_fields = SEARCH_LIST + ('ad_block',)
    list_filter = FILTER_LIST + ('ad_block',)


@admin.register(MusicStat)
class AdStatAdmin(admin.ModelAdmin):
    """Статистики музыки."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST


@admin.register(VideoStat)
class AdStatAdmin(admin.ModelAdmin):
    """Статистики видео."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST


@admin.register(ImageStat)
class AdStatAdmin(admin.ModelAdmin):
    """Статистики картинок."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST


@admin.register(TickerStat)
class AdStatAdmin(admin.ModelAdmin):
    """Статистики бегущей строки."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST
