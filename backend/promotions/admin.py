from django.contrib import admin

from promotions.models import Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'is_active',
        'counterparty',
        'start_period',
        'end_period',
    )
    list_display_links = ('name',)
    search_fields = ("name",)
    list_filter = ('is_active', 'counterparty')
    date_hierarchy = 'created'
    readonly_fields = ("id", "code1c", "created")
