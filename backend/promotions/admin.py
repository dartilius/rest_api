from django.contrib import admin
from django.db.models import Prefetch

from brands.models import Brand
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

    def get_queryset(self, request):
        """Загружает данные для отображения контрагента без N+1 запросов."""
        return (
            Promotion.objects
            .select_related("counterparty")
            .prefetch_related(
                Prefetch(
                    "counterparty__brands",
                    queryset=Brand.objects.only("id", "name"),
                    to_attr="_prefetched_brands",
                ),
            )
        )
