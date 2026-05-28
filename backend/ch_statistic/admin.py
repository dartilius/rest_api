from django.contrib import admin
from django.db.models import Q
from ch_statistic.models import (
    ADStat,
    MusicStat,
    VideoStat,
    ImageStat,
    TickerStat
)
from nomenclatures.models import Nomenclature
from django.core.cache import cache

DISPLAY_LIST = (
    'client',
    'file',
    'played',
    'created',
    'length'
)

SEARCH_LIST = ('client', 'file')
FILTER_LIST = ('client', 'file')

NOMENCLATURE_CACHE_KEY = 'admin_nomenclature_map'
NOMENCLATURE_CACHE_TTL = 60 * 5  # 5 минут


def get_nomenclature_map(uuids: list[str]) -> dict[str, dict]:
    """
    Возвращает словарь uuid → {name, code1c, brand_name}.
    Использует Django cache, чтобы не дёргать PostgreSQL на каждый запрос.
    """
    cached = cache.get(NOMENCLATURE_CACHE_KEY, {})

    missing = [uid for uid in uuids if uid not in cached]
    if missing:
        qs = (
            Nomenclature.objects
            .filter(id__in=missing)
            .select_related('brand')
            .values('id', 'name', 'code1c', 'brand__name')
        )
        for n in qs:
            cached[str(n['id'])] = {
                'name': n['name'] or '—',
                'code1c': n['code1c'] or '',
                'brand': n['brand__name'] or '—',
            }
        cache.set(NOMENCLATURE_CACHE_KEY, cached, NOMENCLATURE_CACHE_TTL)

    return cached

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

    list_display = ('client_name', 'brand_name', 'short_file', 'played', 'created', 'duration')
    search_fields = ('client', 'file')
    list_filter = FILTER_LIST
    show_full_result_count = False

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False

        # если вбили UUID — ищем напрямую
        direct_qs = queryset.filter(client=search_term)
        if direct_qs.exists():
            return direct_qs, False

        # ищем в PostgreSQL по названию и коду
        matched_uuids = list(
            Nomenclature.objects
            .filter(
                Q(name__icontains=search_term) |
                Q(code1c__icontains=search_term)
            )
            .values_list('id', flat=True)
        )
        matched_uuids_str = [str(uid) for uid in matched_uuids]

        if matched_uuids_str:
            get_nomenclature_map(matched_uuids_str)

        return queryset.filter(client__in=matched_uuids_str), False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        uuids = list(qs.values_list('client', flat=True).distinct())
        get_nomenclature_map(uuids)
        return qs

    def _get_nom(self, obj) -> dict:
        nmap = cache.get(NOMENCLATURE_CACHE_KEY, {})
        return nmap.get(str(obj.client), {})

    @admin.display(description='Номенклатура')
    def client_name(self, obj):
        nom = self._get_nom(obj)
        name = nom.get('name', obj.client)
        code = nom.get('code1c', '')
        if code:
            return f'{name} ({code})'
        return name

    @admin.display(description='Бренд')
    def brand_name(self, obj):
        return self._get_nom(obj).get('brand', '—')

    @admin.display(description='Файл')
    def short_file(self, obj):
        return str(obj.file)[:8] + '…'

    @admin.display(description='Длительность')
    def duration(self, obj):
        seconds = int(obj.length or 0)
        return f'{seconds // 60:02d}:{seconds % 60:02d}'

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
