from django.contrib import admin, messages
from django.utils.translation import ngettext

from orders.models import AdOrder, BgOrder, ORDER_TYPES
from orders.tasks import (
    cancel_ad_order_task,
    cancel_bg_order_task,
    create_ad_order_task,
    create_bg_order_task
)


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
    search_fields = (
        'id',
        'name',
        'client',
        'playlist'
    )
    raw_id_fields = ('client', 'playlist', 'owner')
    show_full_result_count = False

    def get_queryset(self, request):
        return AdOrder.objects.all().select_related(
            'owner', 'client', 'playlist'
        )

    def save_model(self, request, obj, form, change):
        """
        Сохранение модели и создание репликации для нового заказа.

        1. Сохраняем объект
        2. Если это создание нового заказа (не изменение)
        3. И статус заказа 0 (Ожидает эфира) или 1 (В эфире)
        4. Запускаем создание репликации
        """
        # 1
        super().save_model(request, obj, form, change)

        # 2, 3
        if not change and obj.status in [0, 1]:
            # 4
            create_ad_order_task.delay([str(obj.id)])

    def save_related(self, request, form, formsets, change):
        """
        Сохранение связанных объектов и создание репликаций
        для множества созданных заказов (если есть).
        """
        super().save_related(request, form, formsets, change)

        # Если это создание и есть сохраненные объекты
        if not change and hasattr(form, 'saved_objects'):
            order_ids = []
            for obj in form.saved_objects:
                if isinstance(obj, AdOrder) and obj.status in [0, 1]:
                    order_ids.append(str(obj.id))

            if order_ids:
                create_ad_order_task.delay(order_ids)

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
            order_ids = [str(order.id) for order in queryset]
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
    search_fields = (
        'id',
        'name',
        'client',
        'playlist'
    )
    raw_id_fields = ('client', 'owner', 'playlist')
    show_full_result_count = False

    def get_queryset(self, request):
        return BgOrder.objects.all().select_related(
            'owner', 'client', 'playlist'
        )

    def save_model(self, request, obj, form, change):
        """
        Сохранение модели и создание репликации для нового заказа.

        1. Сохраняем объект
        2. Если это создание нового заказа (не изменение)
        3. И статус заказа 0 (Ожидает эфира) или 1 (В эфире)
        4. Запускаем создание репликации
        """
        # 1
        super().save_model(request, obj, form, change)

        # 2, 3
        if not change and obj.status in [0, 1]:
            # 4
            create_bg_order_task.delay([str(obj.id)])

    def save_related(self, request, form, formsets, change):
        """
        Сохранение связанных объектов и создание репликаций
        для множества созданных заказов (если есть).

        Это может пригодиться при использовании inline-форм
        или при массовом создании через админку.
        """
        super().save_related(request, form, formsets, change)

        # Если это создание и есть сохраненные объекты
        if not change and hasattr(form, 'saved_objects'):
            order_ids = []
            for obj in form.saved_objects:
                if isinstance(obj, BgOrder) and obj.status in [0, 1]:
                    order_ids.append(str(obj.id))

            if order_ids:
                create_bg_order_task.delay(order_ids)

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
            order_ids = [str(order.id) for order in queryset]
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