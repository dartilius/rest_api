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
    list_display = ["id", "owner", "commercial_status", "duration", "all_days", "created"]
    list_filter = ["all_days", "commercial_status"]
    search_fields = ["owner__email", "owner__first_name", "owner__last_name"]
    readonly_fields = [
        "owner", "created", "qualified_at", "proposal_sent_at", "booked_at", "lost_at",
    ]
    inlines = [PlacementOrderItemInline]

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        return fieldsets + (("Commercial funnel", {
            "fields": (
                "commercial_status", "lost_reason", "attribution", "qualified_at",
                "proposal_sent_at", "booked_at", "lost_at",
            )
        }),)

    fieldsets = (
        ("Основное", {
            "fields": ("owner", "duration")
        }),
        ("Даты размещения", {
            "fields": ("start_date", "end_date")
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
