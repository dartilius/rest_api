from django.contrib import admin

from ch_statistic.models import AD, Music, Video, Image, Ticker

DISPLAY_LIST = (
    'client',
    'value',
    'played',
    'created',
    'length'
)

SEARCH_LIST = (
    'client',
    'value'
)

FILTER_LIST = (
    'client',
    'value'
)

@admin.register(AD)
class AdStatAdmin(admin.ModelAdmin):
    """Статистики рекламы."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST


@admin.register(Music)
class AdStatAdmin(admin.ModelAdmin):
    """Статистики музыки."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST


@admin.register(Video)
class AdStatAdmin(admin.ModelAdmin):
    """Статистики видео."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST


@admin.register(Image)
class AdStatAdmin(admin.ModelAdmin):
    """Статистики картинок."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST


@admin.register(Ticker)
class AdStatAdmin(admin.ModelAdmin):
    """Статистики бегущей строки."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST
