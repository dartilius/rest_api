# orders/admin.py
"""
Административный интерфейс для управления заказами (рекламными и фоновыми).

ОСНОВНЫЕ ВОЗМОЖНОСТИ:
───────────────────────────────────────────────────────────────────────────────
1. Рекламные заказы (AdOrderAdmin):
   - Создание/редактирование заказов с различными типами вещания
   - Отмена заказов с автоматическим созданием репликаций
   - Отображение статусов и интервалов вещания

2. Фоновые заказы (BgOrderAdmin):
   - Поддержка бессрочных заказов (is_permanent)
   - Автоматическое определение типа заказа по плейлисту
   - Массовая отмена заказов
   - Отображение статусов и типов контента

БЕССРОЧНЫЕ ЗАКАЗЫ:
───────────────────────────────────────────────────────────────────────────────
Бессрочный заказ (is_permanent=True) — это заказ без даты окончания.
Он используется как "запасной" плейлист, который играет когда нет
активных заказов с датами.

Приоритеты воспроизведения:
1. Заказы с датами, попадающие в текущий период — ВЫСОКИЙ приоритет
2. Бессрочный заказ — НИЗКИЙ приоритет (играет при отсутствии срочных)

Для бессрочного заказа:
- broadcast_interval может быть пустым или содержать только дату начала
- is_permanent = True
- При создании репликации broadcast_end не передаётся (None)
"""

from django.contrib import admin, messages
from django.utils.translation import ngettext

from orders.models import AdOrder, BgOrder, ORDER_TYPES
from orders.tasks import (
    cancel_ad_order_task,
    cancel_bg_order_task,
    create_ad_order_task,
    create_bg_order_task
)


# ═══════════════════════════════════════════════════════════════════════════════
# РЕКЛАМНЫЕ ЗАКАЗЫ (AdOrderAdmin)
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(AdOrder)
class AdOrderAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления рекламными заказами.

    Рекламные заказы поддерживают 7 типов вещания (broadcast_type: 0-6):
    0 - По времени работы точки
    1 - Начало работы + смещение
    2 - Конец работы - смещение
    3 - Конкретные часы
    4 - Открытие до часа
    5 - Час до закрытия
    6 - По событию
    """

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

    search_fields = ('id', 'name', 'client', 'playlist')
    raw_id_fields = ('client', 'playlist', 'owner')
    show_full_result_count = False

    def get_queryset(self, request):
        """Оптимизация запросов с предзагрузкой связанных объектов."""
        return AdOrder.objects.all().select_related(
            'owner', 'client', 'playlist'
        )

    def save_model(self, request, obj, form, change):
        """
        Сохранение заказа и автоматическое создание репликации.

        При создании нового заказа (change=False) со статусом
        "Ожидает эфира" или "В эфире" автоматически запускается
        задача на создание репликации для отправки на клиент.
        """
        super().save_model(request, obj, form, change)

        if not change and obj.status in [0, 1]:
            create_ad_order_task.delay([str(obj.id)])

    def save_related(self, request, form, formsets, change):
        """
        Сохранение связанных объектов и создание репликаций
        для множества созданных заказов.
        """
        super().save_related(request, form, formsets, change)

        if not change and hasattr(form, 'saved_objects'):
            order_ids = []
            for obj in form.saved_objects:
                if isinstance(obj, AdOrder) and obj.status in [0, 1]:
                    order_ids.append(str(obj.id))

            if order_ids:
                create_ad_order_task.delay(order_ids)

    @admin.action(description='❌ Отменить выбранные заказы')
    def cancel(self, request, queryset):
        """
        Массовая отмена рекламных заказов.

        1. Проверяет, что среди выбранных нет уже отменённых/завершённых
        2. Устанавливает статус "Отменён" (3)
        3. Создаёт репликации на отмену для каждого заказа
        """
        if queryset.filter(status__in=[2, 3, 4]).exists():
            self.message_user(
                request,
                'Среди выбранных заказов есть такие, которые отменить нельзя',
                messages.ERROR
            )
            return

        updated = queryset.update(status=3)
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


# ═══════════════════════════════════════════════════════════════════════════════
# ФОНОВЫЕ ЗАКАЗЫ (BgOrderAdmin)
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(BgOrder)
class BgOrderAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления фоновыми заказами.

    Типы фоновых заказов (order_type):
    0 - Фоновая музыка
    1 - Фоновые видео
    2 - Фоновые картинки
    3 - Бегущая строка

    БЕССРОЧНЫЕ ЗАКАЗЫ (is_permanent):
    ───────────────────────────────────────────────────────────────────────────
    Бессрочный заказ — это заказ без даты окончания, который используется
    как резервный плейлист. Он автоматически включается когда нет активных
    заказов с датами (срочных).

    Для создания бессрочного заказа:
    1. Установите флаг "Бессрочный заказ"
    2. broadcast_interval можно оставить пустым или указать только дату начала

    Приоритеты воспроизведения на клиенте:
    1. Срочные заказы с датами (is_permanent=False) — ВЫСОКИЙ
    2. Бессрочный заказ (is_permanent=True) — НИЗКИЙ
    """

    actions = ['cancel']

    @admin.display(description='Тип')
    def order_type_display(self, obj):
        """Отображает тип заказа в человеко-читаемом виде."""
        return ORDER_TYPES.get(obj.order_type, f'Тип {obj.order_type}')

    @admin.display(description='Бессрочный', boolean=True)
    def is_permanent_display(self, obj):
        """Отображает флаг бессрочности заказа."""
        return obj.is_permanent

    def get_readonly_fields(self, request, obj=None):
        """
        При редактировании существующего заказа тип заказа (order_type)
        становится недоступным для изменения.
        """
        if obj:
            return ['order_type']
        return []

    list_display = (
        'id',
        'order_type_display',
        'name',
        'status',
        'client',
        'is_permanent_display',  # 🔥 Отображение флага бессрочности
        'playlist',
        'owner',
        'created'
    )

    list_filter = (
        'order_type',  # Тип контента
        'status',  # Статус заказа
        'is_permanent',  # 🔥 Фильтр по бессрочным заказам
        'created',  # Дата создания
    )

    search_fields = ('id', 'name', 'client', 'playlist')
    raw_id_fields = ('client', 'owner', 'playlist')
    show_full_result_count = False

    # 🔥 Группировка полей с учётом бессрочных заказов
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'order_type', 'status', 'owner')
        }),
        ('♾️ Тип заказа', {
            'fields': ('is_permanent',),
            'description': (
                '<div style="padding: 10px; background: #f0f7ff; border-radius: 8px; '
                'border-left: 4px solid #2196F3; margin-bottom: 10px;">'
                '<strong>💡 О бессрочных заказах:</strong><br>'
                'Бессрочный заказ играет когда нет активных заказов с датами.<br>'
                'Используется как "запасной" плейлист для непрерывного вещания.'
                '</div>'
            )
        }),
        ('Клиент и плейлист', {
            'fields': ('client', 'playlist')
        }),
        ('📅 Интервал вещания', {
            'fields': ('broadcast_interval',),
            'description': (
                'Для <strong>срочных</strong> заказов — укажите дату начала и окончания.<br>'
                'Для <strong>бессрочных</strong> — можно оставить пустым или указать только дату начала.'
            )
        }),
        ('Параметры', {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Оптимизация запросов с предзагрузкой связанных объектов."""
        return BgOrder.objects.all().select_related(
            'owner', 'client', 'playlist'
        )

    def save_model(self, request, obj, form, change):
        """
        Сохранение заказа и автоматическое создание репликации.

        При создании нового заказа (change=False) со статусом
        "Ожидает эфира" или "В эфире" автоматически запускается
        задача на создание репликации.

        Для бессрочных заказов в репликацию передаётся:
        - is_permanent = True
        - broadcast_end = None
        """
        super().save_model(request, obj, form, change)

        if not change and obj.status in [0, 1]:
            create_bg_order_task.delay([str(obj.id)])

    def save_related(self, request, form, formsets, change):
        """
        Сохранение связанных объектов и создание репликаций
        для множества созданных заказов.
        """
        super().save_related(request, form, formsets, change)

        if not change and hasattr(form, 'saved_objects'):
            order_ids = []
            for obj in form.saved_objects:
                if isinstance(obj, BgOrder) and obj.status in [0, 1]:
                    order_ids.append(str(obj.id))

            if order_ids:
                create_bg_order_task.delay(order_ids)

    @admin.action(description='❌ Отменить выбранные заказы')
    def cancel(self, request, queryset):
        """
        Массовая отмена фоновых заказов.

        1. Проверяет, что среди выбранных нет уже отменённых/завершённых
        2. Устанавливает статус "Отменён" (3)
        3. Создаёт репликации на отмену для каждого заказа
        """
        if queryset.filter(status__in=[2, 3, 4]).exists():
            self.message_user(
                request,
                'Среди выбранных заказов есть такие, которые отменить нельзя',
                messages.ERROR
            )
            return

        updated = queryset.update(status=3)
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
