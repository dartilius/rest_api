from django.contrib import admin

from orders.models import AdOrder, BgOrder


@admin.register(AdOrder)
class AdOrderAdmin(admin.ModelAdmin):
    """Рекламный заказ."""

    list_display = (
        'id',
        'owner',
        'name',
        'description',
        'group',
        'broadcast_interval',
        'file',
        'created'
    )
    search_fields = (
        'id',
        'name',
        'group',
        'file'
    )

    def get_queryset(self, request):
        return AdOrder.objects.all().select_related('owner', 'group', 'file')


@admin.register(BgOrder)
class BgOrderAdmin(admin.ModelAdmin):
    """Фоновый заказ."""

    list_display = (
        'id',
        'owner',
        'name',
        'description',
        'client',
        'playlist',
        'created'
    )
    search_fields = (
        'id',
        'name',
        'client',
        'playlist'
    )

    def get_queryset(self, request):
        return BgOrder.objects.all().select_related(
            'owner', 'client', 'playlist'
        )
