from django.contrib import admin

from orders.models import AdOrder, BgOrder, ORDER_TYPES


@admin.register(AdOrder)
class AdOrderAdmin(admin.ModelAdmin):
    """Рекламный заказ."""

    list_display = (
        'id',
        'name',
        'status',
        'group',
        'broadcast_interval',
        'file',
        'owner',
        'created'
    )
    list_filter = (
        'owner',
        'group',
        'status',
        'broadcast_interval',
        'created'
    )
    search_fields = (
        'id',
        'name',
        'group',
        'file'
    )

    def get_queryset(self, request):
        return AdOrder.objects.all().select_related(
            'owner', 'group', 'file'
        )


@admin.register(BgOrder)
class BgOrderAdmin(admin.ModelAdmin):
    """Фоновый заказ."""

    @admin.display
    def order_type(self, obj):
        return ORDER_TYPES[obj.order_type]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['order_type']
        else:
            return []

    list_display = (
        'id',
        'order_type',
        'name',
        'status',
        'group',
        'playlist',
        'owner',
        'created'
    )
    list_filter = (
        'owner',
        'group',
        'order_type',
        'status',
        'broadcast_interval',
        'created'
    )
    search_fields = (
        'id',
        'name',
        'group',
        'playlist'
    )

    def get_queryset(self, request):
        return BgOrder.objects.all().select_related(
            'owner', 'group', 'playlist'
        )
