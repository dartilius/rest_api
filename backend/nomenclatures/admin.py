from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Prefetch, Count
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import prefetch_related_objects

from nomenclatures.models import (
    Nomenclature,
    NomenclatureAvailability,
    StatusHistory,
    STATUSES,
    NomenclatureImage,
    NomenclatureAddress,
    TypeOfPlace,
    NomenclatureTenant
)


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    """Номенклатура — полностью оптимизированная версия с сохранением подсчета"""

    # ========== ОСНОВНЫЕ НАСТРОЙКИ ==========
    list_display = (
        "id_short",                # сокращенный ID для компактности
        "name",
        "owner_name",              # кастомное поле вместо owner
        "timezone",
        "is_active",
        "status_display",           # кастомное поле статуса
        "code1c",
        "brand_name",               # кастомное поле бренда
        "legal_entity_name",        # кастомное поле юрлица
        "tenants_count_display",    # количество арендаторов
    )

    list_display_links = ("name",)  # только название как ссылка

    search_fields = ("name", "code1c", "article")
    list_filter = ("is_active", "timezone", "brand", "contentType")

    # ✅ ПОДСЧЕТ ВКЛЮЧЕН (как вы просили)
    show_full_result_count = True

    # Уменьшаем количество записей на странице для скорости
    list_per_page = 50

    # Поля с автодополнением (для быстрого поиска)
    autocomplete_fields = ['owner', 'brand', 'legalEntity', 'responsible_radio']

    # Поля с ID вместо выпадающих списков (для очень больших таблиц)
    raw_id_fields = ('owner', 'brand', 'legalEntity')

    # ========== ОПТИМИЗАЦИЯ QUERYSET ДЛЯ СПИСКА ==========
    def get_queryset(self, request):
        """Загружаем все связанные данные одним запросом с кэшированием"""

        # Пробуем взять из кэша
        cache_key = f"nomenclature_admin_qs_{request.user.id}"
        qs = cache.get(cache_key)

        if not qs:
            qs = super().get_queryset(request).select_related(
                # ForeignKey поля — загружаем через JOIN
                "owner",
                "availability",
                "brand",
                "legalEntity",
                "responsible_radio",
                "responsible_ad",
            ).prefetch_related(
                # ManyToMany поля — загружаем отдельным запросом
                "tenants",
                # Только одно фото для предпросмотра
                Prefetch(
                    "images",
                    queryset=NomenclatureImage.objects.filter(type="exterior")[:1],
                    to_attr="prefetched_exterior"
                ),
            ).annotate(
                # Вычисляемые поля прямо в SQL
                tenants_count=Count("tenants", distinct=True),
            ).only(
                # Загружаем только нужные поля (экономия памяти)
                # Поля самой номенклатуры
                'id', 'name', 'timezone', 'is_active', 'code1c', 'article',

                # Поля владельца
                'owner__email', 'owner__first_name', 'owner__last_name',

                # Поля доступности
                'availability__status', 'availability__last_answer_date',

                # Поля бренда
                'brand__name',

                # Поля юрлица
                'legalEntity__first_name', 'legalEntity__middle_name',
                'legalEntity__last_name', 'legalEntity__keyword',

                # Поля ответственных (ВАЖНО: добавляем все, что используем в select_related)
                'responsible_radio__email', 'responsible_radio__first_name', 'responsible_radio__last_name',
                'responsible_ad__email', 'responsible_ad__first_name', 'responsible_ad__last_name',
            )

            # Сохраняем в кэш на 5 минут
            cache.set(cache_key, qs, 300)

        return qs

    # ========== ОПТИМИЗАЦИЯ ФОРМЫ РЕДАКТИРОВАНИЯ ==========
    # Именно здесь была главная проблема — 3793 запроса!

    def get_object(self, request, object_id, from_field=None):
        """
        Полностью переопределяем загрузку объекта для формы редактирования.
        Без этой оптимизации каждый связанный объект вызывает отдельный запрос.
        """
        # Получаем объект стандартным способом
        obj = super().get_object(request, object_id, from_field)

        if obj:
            # Пробуем взять из кэша
            cache_key = f"nomenclature_obj_full_{obj.pk}"
            cached = cache.get(cache_key)

            if not cached:
                # Если нет в кэше — загружаем ВСЕ связанные объекты ОДНИМ запросом
                # Это ключевой момент! prefetch_related_objects загружает всё сразу
                prefetch_related_objects(
                    [obj],
                    # ForeignKey поля
                    'owner',
                    'brand',
                    'legalEntity',
                    'responsible_radio',
                    'responsible_ad',
                    'responsible_technic',
                    'responsible_technic_on_address',
                    'responsible_placement_marketing',
                    'availability',
                    # ManyToMany поля
                    'tenants',
                    # Фотографии (только последние 5 для превью)
                    Prefetch(
                        'images',
                        queryset=NomenclatureImage.objects.order_by('-created')[:5],
                        to_attr='prefetched_images'
                    ),
                )

                # Сохраняем в кэш на 5 минут
                cache.set(cache_key, True, 300)

        return obj

    def get_form(self, request, obj=None, **kwargs):
        """
        Оптимизация формы — убираем лишние запросы при отображении полей.
        """
        form = super().get_form(request, obj, **kwargs)

        if obj:
            # Убеждаемся, что объект уже загружен со всеми связанными данными
            # Если нет — загружаем через get_object (который уже оптимизирован)
            if not hasattr(obj, '_prefetched_objects_cache'):
                obj = self.get_object(request, obj.pk)

        return form

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """
        Добавляем информацию о кэше в контекст для отладки (опционально).
        """
        if obj and hasattr(obj, '_prefetched_objects_cache'):
            # Можно добавить информацию о кэше в контекст
            context['cached_fields'] = list(obj._prefetched_objects_cache.keys())

        return super().render_change_form(request, context, add, change, form_url, obj)

    # ========== КАСТОМНЫЕ ПОЛЯ ДЛЯ LIST_DISPLAY ==========

    @admin.display(description="ID", ordering="id")
    def id_short(self, obj):
        """Сокращенный ID для компактности"""
        return str(obj.id)[:8] + "..."

    @admin.display(description="Владелец", ordering="owner__email")
    def owner_name(self, obj):
        """
        Безопасное получение имени владельца.
        Если нет email — используем имя или возвращаем прочерк.
        """
        if not obj.owner:
            return "-"

        if hasattr(obj.owner, 'full_name') and obj.owner.full_name:
            return obj.owner.full_name
        elif obj.owner.email:
            return obj.owner.email
        else:
            return f"ID:{str(obj.owner.id)[:8]}"

    @admin.display(description="Статус", ordering="availability__status")
    def status_display(self, obj):
        """Статус с цветовой индикацией"""
        try:
            status_code = obj.availability.status
            status_text = STATUSES[obj.availability.status]

            colors = {
                0: "green",   # Online
                1: "orange",  # Offline 5+ minutes
                2: "red",     # Offline 1+ hour
            }
            color = colors.get(status_code, "gray")

            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, status_text
            )
        except (AttributeError, KeyError):
            return "Нет данных"

    @admin.display(description="Бренд", ordering="brand__name")
    def brand_name(self, obj):
        return obj.brand.name if obj.brand else "-"

    @admin.display(description="Юр.лицо", ordering="legalEntity__name")
    def legal_entity_name(self, obj):
        """Безопасное получение названия юрлица"""
        if not obj.legalEntity:
            return "-"

        if hasattr(obj.legalEntity, 'name'):
            return obj.legalEntity.name
        else:
            return f"ID:{str(obj.legalEntity.id)[:8]}"

    @admin.display(description="Арендаторы")
    def tenants_count_display(self, obj):
        """Количество арендаторов с ссылкой на фильтр"""
        count = getattr(obj, 'tenants_count', 0)
        if count > 0:
            url = f"/admin/nomenclatures/nomenclature/{obj.id}/change/"
            return format_html('<a href="{}">{} шт.</a>', url, count)
        return "0"

    # ========== ДЕЙСТВИЯ ==========
    actions = ['activate', 'deactivate', 'clear_cache']

    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано {updated} номенклатур')
        # Инвалидируем кэш
        cache.delete_pattern("nomenclature_admin_qs_*")
    activate.short_description = "Активировать выбранные"

    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано {updated} номенклатур')
        # Инвалидируем кэш
        cache.delete_pattern("nomenclature_admin_qs_*")
    deactivate.short_description = "Деактивировать выбранные"

    def clear_cache(self, request, queryset):
        """Очистить кэш"""
        cache.delete_pattern("nomenclature_admin_qs_*")
        self.message_user(request, 'Кэш очищен')
    clear_cache.short_description = "Очистить кэш"


@admin.register(NomenclatureTenant)
class NomenclatureTenantAdmin(admin.ModelAdmin):
    """Арендаторы номенклатур — оптимизированная версия с сохранением подсчета"""

    list_display = ("nomenclature_name", "tenant_id", "floor")
    search_fields = ("nomenclature__name", "tenant_id")
    show_full_result_count = True  # Подсчет включен
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("nomenclature")

    @admin.display(description="Номенклатура", ordering="nomenclature__name")
    def nomenclature_name(self, obj):
        return obj.nomenclature.name if obj.nomenclature else "-"


@admin.register(TypeOfPlace)
class TypeOfPlaceAdmin(admin.ModelAdmin):
    """Тип места вещания"""

    list_display = ("id", "name", "is_active")
    search_fields = ("name", "prepositional", "genitive", "abbreviation")
    show_full_result_count = True

    def get_queryset(self, request):
        return TypeOfPlace.objects.all()

@admin.register(NomenclatureAvailability)
class NomenclatureAvailabilityAdmin(admin.ModelAdmin):
    """Доступность — оптимизированная версия с сохранением подсчета"""

    list_display = ("client_name", "last_answer_date", "status_display")
    list_filter = ("status",)
    search_fields = ("client__name", "client__code1c")
    show_full_result_count = True  # Подсчет включен
    raw_id_fields = ("client",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("client").only(
            'client__name', 'client__id',
            'last_answer_date', 'status'
        )

    @admin.display(description="Номенклатура", ordering="client__name")
    def client_name(self, obj):
        return obj.client.name if obj.client else "-"

    @admin.display(description="Статус")
    def status_display(self, obj):
        status_text = STATUSES.get(obj.status, "Неизвестно")
        colors = {0: "green", 1: "orange", 2: "red"}
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: {};">{}</span>',
            color, status_text
        )


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    """История доступности — оптимизированная версия с сохранением подсчета"""

    list_display = ("client_name", "change_time", "status_display")
    list_filter = ("status", "change_time")
    search_fields = ("client__name",)
    show_full_result_count = True  # Подсчет включен
    raw_id_fields = ("client",)
    list_per_page = 100

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("client").only(
            'client__name', 'client__id',
            'change_time', 'status'
        )

    @admin.display(description="Номенклатура", ordering="client__name")
    def client_name(self, obj):
        return obj.client.name if obj.client else "-"

    @admin.display(description="Статус")
    def status_display(self, obj):
        return STATUSES.get(obj.status, "Неизвестно")


@admin.register(NomenclatureImage)
class NomenclatureImageAdmin(admin.ModelAdmin):
    """Фотографии номенклатур — оптимизированная версия с сохранением подсчета"""

    list_display = ("id_short", "nomenclature_name", "type", "created", "hash_short")
    list_filter = ("type", "created")
    search_fields = ("nomenclature__name", "hash")
    show_full_result_count = True  # Подсчет включен
    raw_id_fields = ("nomenclature",)
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("nomenclature").only(
            'id', 'type', 'created', 'hash',
            'nomenclature__name', 'nomenclature__id'
        )

    @admin.display(description="ID")
    def id_short(self, obj):
        return str(obj.id)[:8] + "..."

    @admin.display(description="Номенклатура", ordering="nomenclature__name")
    def nomenclature_name(self, obj):
        return obj.nomenclature.name if obj.nomenclature else "-"

    @admin.display(description="Хэш")
    def hash_short(self, obj):
        return f"{obj.hash[:8]}..." if obj.hash else "-"


@admin.register(NomenclatureAddress)
class NomenclatureAddressAdmin(admin.ModelAdmin):
    """Адреса номенклатур — оптимизированная версия с сохранением подсчета"""

    list_display = ("nomenclature_name", "address_short")
    search_fields = ("nomenclature__name", "address__city__name", "address__street__name", "address__house__number")  # Исправлено
    show_full_result_count = True
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "nomenclature",
            "address",
            "address__city",      # Добавлено для str
            "address__street",    # Добавлено для str
            "address__house",     # Добавлено для str
            "address__building"   # Добавлено для str
        ).only(
            'nomenclature__name', 'nomenclature__id',
            # Поля для address.__str__
            'address__id',
            'address__city__name',
            'address__street__name',
            'address__house__number',
            'address__building__number'
        )

    @admin.display(description="Номенклатура", ordering="nomenclature__name")
    def nomenclature_name(self, obj):
        return obj.nomenclature.name if obj.nomenclature else "-"

    @admin.display(description="Адрес")
    def address_short(self, obj):
        if not obj.address:
            return "-"
        return str(obj.address)[:50]


# ========== ИНВАЛИДАЦИЯ КЭША ПРИ ИЗМЕНЕНИЯХ ==========
@receiver(post_save, sender=Nomenclature)
@receiver(post_delete, sender=Nomenclature)
def invalidate_nomenclature_cache(sender, **kwargs):
    """Очищаем кэш при сохранении или удалении номенклатуры"""
    cache.delete_pattern("nomenclature_admin_qs_*")
    # Также очищаем кэш конкретных объектов
    if 'instance' in kwargs:
        cache.delete(f"nomenclature_obj_full_{kwargs['instance'].pk}")
