from django.contrib import admin

from orders.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Заказ."""

    list_display = (
        'id',
        'owner',
        'name',
        'description',
        'group',
        'type',
        'broadcast_interval',
        'playlist',
        'created'
    )
    search_fields = (
        'id',
        'name',
        'group',
        'type',
        'playlist'
    )

    def get_queryset(self, request):
        return Order.objects.all().select_related('owner')
