from django.contrib import admin, messages
from django.utils.translation import ngettext

from orders.models import AdOrder, BgOrder, ORDER_TYPES
from orders.tasks import cancel_ad_order_task, cancel_bg_order_task


@admin.register(AdOrder)
class AdOrderAdmin(admin.ModelAdmin):
    """Рекламный заказ."""

    actions = ['cancel']

    list_display = (
        'id',
        'name',
        'status',
        'client',
        'broadcast_interval',
        'playlist',
        'owner',
        'created'
    )
    list_filter = (
        'owner',
        'client',
        'status',
        'broadcast_interval',
        'created'
    )
    search_fields = (
        'id',
        'name',
        'client',
        'playlist'
    )

    def get_queryset(self, request):
        return AdOrder.objects.all().select_related(
            'owner', 'client', 'playlist'
        )

    @admin.action(description='Отменить выбранные заказы')
    def cancel(self, request, queryset):
        """
        Отмена заказов.

        1. Если среди выбранных заказов есть такие, которые отменить нельзя, то
            очищаем queryset и выдаём сообщение об ошибке.
        2. Если всё ок, выбранным заказам выставляемся статус Отменён.
        3. Собираются айди заказов и отправляются в целери
            для создания репликаций.
        """
        # 1
        if queryset.filter(status__in=[2, 3, 4]).exists():
            self.message_user(
                request,
                f'Среди выбранных заказов есть такие, '
                f'которые отменить нельзя',
                messages.ERROR
            )
            queryset = None
        try:
            # 2
            updated = queryset.update(status=3)
            # 3
            order_ids = [order.id for order in queryset]
            cancel_ad_order_task.delay(order_ids)
            self.message_user(
                request,
                ngettext(
                    f'{updated} запрос на отмену заказа принят',
                    f'{updated} запросов на отмену заказов принято',
                    updated,
                ),
                messages.SUCCESS
            )
        except AttributeError:
            pass


@admin.register(BgOrder)
class BgOrderAdmin(admin.ModelAdmin):
    """Фоновый заказ."""

    actions = ['cancel']

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
        'client',
        'playlist',
        'owner',
        'created'
    )
    list_filter = (
        'owner',
        'client',
        'order_type',
        'status',
        'broadcast_interval',
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

    @admin.action(description='Отменить выбранные заказы')
    def cancel(self, request, queryset):
        """
        Отмена заказов.

        1. Если среди выбранных заказов есть такие, которые отменить нельзя, то
            очищаем queryset и выдаём сообщение об ошибке.
        2. Если всё ок, выбранным заказам выставляемся статус Отменён.
        3. Собираются айди заказов и отправляются в целери
            для создания репликаций.
        """
        # 1
        if queryset.filter(status__in=[2, 3, 4]).exists():
            self.message_user(
                request,
                f'Среди выбранных заказов есть такие, '
                f'которые отменить нельзя',
                messages.ERROR
            )
            queryset = None
        try:
            # 2
            updated = queryset.update(status=3)
            # 3
            order_ids = [order.id for order in queryset]
            cancel_bg_order_task.delay(order_ids)
            self.message_user(
                request,
                ngettext(
                    f'{updated} запрос на отмену заказа принят',
                    f'{updated} запросов на отмену заказов принято',
                    updated,
                ),
                messages.SUCCESS
            )
        except AttributeError:
            pass
