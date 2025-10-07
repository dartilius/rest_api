from django.contrib import admin
from django.utils.translation import gettext_lazy as _
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
    'client',  # Вернули обратно, так как в ClickHouse моделях нет __name полей
    'file'     # Вернули обратно, так как в ClickHouse моделях нет __name полей
)

FILTER_LIST = (
    'client',
    'file'
)


class BaseStatAdmin(admin.ModelAdmin):
    """Базовый класс админки для статистики."""

    show_full_result_count = False
    list_per_page = 50
    # Убрали date_hierarchy, так как ClickHouse Backend может не поддерживать его
    # date_hierarchy = 'played'

    def get_queryset(self, request):
        """Оптимизация queryset."""
        qs = super().get_queryset(request)
        return qs


@admin.register(ADStat)
class AdStatAdmin(BaseStatAdmin):
    """Админка статистики рекламы."""

    list_display = DISPLAY_LIST + ('ad_block', 'get_ad_block_display')
    search_fields = SEARCH_LIST + ('ad_block',)
    list_filter = FILTER_LIST + ('ad_block', 'played')

    @admin.display(description="Блок рекламы", ordering='ad_block')
    def get_ad_block_display(self, obj):
        """Отображает ad_block в читаемом формате времени."""
        from datetime import timedelta
        return str(timedelta(seconds=obj.ad_block))


@admin.register(MusicStat)
class MusicStatAdmin(BaseStatAdmin):
    """Админка статистики музыки."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST + ('played',)


@admin.register(VideoStat)
class VideoStatAdmin(BaseStatAdmin):
    """Админка статистики видео."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST + ('played',)


@admin.register(ImageStat)
class ImageStatAdmin(BaseStatAdmin):
    """Админка статистики картинок."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST + ('played',)


@admin.register(TickerStat)
class TickerStatAdmin(BaseStatAdmin):
    """Админка статистики бегущей строки."""

    list_display = DISPLAY_LIST
    search_fields = SEARCH_LIST
    list_filter = FILTER_LIST + ('played',)
