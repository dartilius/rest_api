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
    show_full_result_count = False


@admin.register(MusicStat)
class MusicStatAdmin(admin.ModelAdmin):
    """Статистики музыки."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST
    show_full_result_count = False


@admin.register(VideoStat)
class VideoStatAdmin(admin.ModelAdmin):
    """Статистики видео."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST
    show_full_result_count = False


@admin.register(ImageStat)
class ImageStatAdmin(admin.ModelAdmin):
    """Статистики картинок."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST
    show_full_result_count = False


@admin.register(TickerStat)
class TickerStatAdmin(admin.ModelAdmin):
    """Статистики бегущей строки."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST
    show_full_result_count = False
