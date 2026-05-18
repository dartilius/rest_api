# admin.py

from django.contrib import admin
from .models import PlacementOrder, PlacementOrderItem


class PlacementOrderItemInline(admin.TabularInline):
    model = PlacementOrderItem
    extra = 0
    readonly_fields = ["responsible"]
    fields = ["nomenclature", "responsible"]


@admin.register(PlacementOrder)
class PlacementOrderAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "duration", "all_days", "created"]
    list_filter = ["all_days"]
    search_fields = ["owner__email", "owner__first_name", "owner__last_name"]
    readonly_fields = ["owner", "created"]
    inlines = [PlacementOrderItemInline]

    fieldsets = (
        ("Основное", {
            "fields": ("owner", "duration")
        }),
        ("Дни размещения", {
            "fields": ("all_days", "days_of_week")
        }),
        ("Служебное", {
            "fields": ("created",)
        }),
    )


@admin.register(PlacementOrderItem)
class PlacementOrderItemAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "nomenclature", "responsible"]
    search_fields = ["nomenclature__name", "responsible__email"]
    readonly_fields = ["responsible"]