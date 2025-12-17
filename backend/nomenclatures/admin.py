from django.contrib import admin

from nomenclatures.models import (
    Nomenclature,
    NomenclatureAvailability,
    StatusHistory,
    STATUSES,
    NomenclatureImage,
    NomenclatureAddress,
)


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    """Номенклатура."""

    @admin.display(description="Статус")
    def status(self, obj):
        try:
            return STATUSES[obj.availability.status]
        except AttributeError:
            return None

    list_display = ("id", "name", "owner", "timezone", "is_active", "status", "code1c")
    search_fields = ("name",)
    show_full_result_count = False
    raw_id_fields = ("owner",)

    def get_queryset(self, request):
        return Nomenclature.objects.all().select_related(
            "owner", "availability"
        )


@admin.register(NomenclatureAvailability)
class NomenclatureAvailabilityAdmin(admin.ModelAdmin):
    """Доступность."""

    list_display = ("client", "last_answer_date", "status")
    show_full_result_count = False
    raw_id_fields = ("client",)

    def get_queryset(self, request):
        return NomenclatureAvailability.objects.all().select_related("client")


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    """История доступности."""

    list_display = ("client", "change_time", "status")
    show_full_result_count = False
    raw_id_fields = ("client",)

    def get_queryset(self, request):
        return StatusHistory.objects.all().select_related("client")

@admin.register(NomenclatureImage)
class NomenclatureImageAdmin(admin.ModelAdmin):
    """Администрирование фотографий номенклатур."""

    list_display = ("id", "nomenclature__name", "created")
    search_fields = ("nomenclature__name",)
    show_full_result_count = False
    raw_id_fields = ("nomenclature",)

    def get_queryset(self, request):
        return NomenclatureImage.objects.select_related("nomenclature")


@admin.register(NomenclatureAddress)
class NomenclatureAddressAdmin(admin.ModelAdmin):
    """Администрирование адресов номенклатур."""

    list_display = ("nomenclature_id", "address")
    show_full_result_count = False

    def get_queryset(self, request):
        return NomenclatureAddress.objects.select_related("nomenclature", "address")