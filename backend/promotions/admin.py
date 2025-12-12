from django.contrib import admin

from promotions.models import Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'is_active',
        'counterparty_count'
    )
    search_fields = ("name",)
    readonly_fields = ("id", "code1c", "created")

    def get_queryset(self, request):
        return Promotion.objects.all()
