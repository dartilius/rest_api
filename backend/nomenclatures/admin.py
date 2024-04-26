from django.contrib import admin

from nomenclatures.models import (
    Nomenclature,
    Settings,
    HardWareInfo,
    NomenclatureGroup,
    StatusHistory
)


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    """Номенклатура."""

    list_display = (
        'id',
        'name',
        'owner',
        'timezone',
        'is_active',
        'status'
    )
    search_fields = (
        'id',
        'name',
        'status',
        'timezone',
        'is_active'
    )

    def get_queryset(self, request):
        return Nomenclature.objects.all().select_related(
            'owner'
        ).prefetch_related('settings')


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    """Настройки."""

    list_display = ('days', )


@admin.register(HardWareInfo)
class HardWareInfoAdmin(admin.ModelAdmin):
    """Информация о железе разбы."""

    list_display = ('client',)

    def get_queryset(self, request):
        return HardWareInfo.objects.all().select_related('client')


@admin.register(NomenclatureGroup)
class NomenclatureGroupAdmin(admin.ModelAdmin):
    """Группы."""

    list_display = ('name',)

    def get_queryset(self, request):
        return NomenclatureGroup.objects.all().prefetch_related(
            'clients'
        ).select_related('owner')


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    """История доступности."""

    list_display = (
        'client',
        'change_time',
        'status'
    )

    def get_queryset(self, request):
        return StatusHistory.objects.all().select_related('client')
