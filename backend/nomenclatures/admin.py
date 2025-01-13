from django.contrib import admin

from nomenclatures.models import (
    Nomenclature,
    NomenclatureAvailability,
    StatusHistory,
    STATUSES
)


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    """Номенклатура."""

    @admin.display(description='Статус')
    def status(self, obj):
        try:
            return STATUSES[obj.availability.status]
        except AttributeError:
            return None

    list_display = (
        'id',
        'name',
        'owner',
        'timezone',
        'is_active',
        'status'
    )
    search_fields = ('name',)

    def get_queryset(self, request):
        return Nomenclature.objects.all().select_related(
            'owner', 'availability'
        )


@admin.register(NomenclatureAvailability)
class NomenclatureAvailabilityAdmin(admin.ModelAdmin):
    """Доступность."""

    list_display = ('client', 'last_answer_date', 'status')

    def get_queryset(self, request):
        return NomenclatureAvailability.objects.all().select_related('client')


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
