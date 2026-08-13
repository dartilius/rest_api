"""
Административный интерфейс для модели Nomenclature.

ОПТИМИЗАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ:
───────────────────────────────────────────────────────────────────────────────
1. Использование select_related для всех FK связей (1 запрос вместо N)
2. Использование prefetch_related для всех M2M связей (1 запрос вместо N)
3. Кеширование ID результатов для уменьшения размера кеша
4. Оптимизация list_display для исключения отдельных запросов к БД
5. Поиск без search_vector для ускорения админки
6. Устранение дублирующихся запросов в get_form и render_change_form
"""

from django.contrib import admin
from django.core.cache import cache
from django.db.models import Prefetch, Count, Q
from django.db.models import prefetch_related_objects
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.html import format_html
from django.http import JsonResponse
from django.utils.dateparse import parse_date

from ch_statistic.models import MusicStat
from nomenclatures.models import (
    Nomenclature,
    NomenclatureAvailability,
    StatusHistory,
    STATUSES,
    NomenclatureImage,
    NomenclatureAddress,
    TypeOfPlace,
    NomenclatureTenant,
    DiscountRule
)


class DiscountRuleInline(admin.TabularInline):
    """
    Inline-форма для правил скидок в административной панели.
    """
    model = DiscountRule
    extra = 1
    fields = ("days_from", "days_to", "coefficient")
    ordering = ("days_from",)


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Nomenclature.
    """

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                '<uuid:object_id>/music-stat/',
                self.admin_site.admin_view(self.music_stat_view),
                name='nomenclature_music_stat',
            ),
        ]
        return custom + urls

    def music_stat_view(self, request, object_id):
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        if not date_from or not date_to:
            return JsonResponse({'error': 'Укажите date_from и date_to'}, status=400)

        parsed_from = parse_date(date_from)
        parsed_to = parse_date(date_to)

        if not parsed_from or not parsed_to:
            return JsonResponse({'error': 'Неверный формат даты'}, status=400)

        queryset = (
            MusicStat.objects
            .filter(
                client=str(object_id),
                played__date__gte=parsed_from,
                played__date__lte=parsed_to,
            )
            .order_by('-played')
            .values('file', 'played', 'length')[:200]
        )

        results = [
            {
                'file': row['file'],
                'played': row['played'].strftime('%Y-%m-%d %H:%M:%S'),
                'played_krasnoyarsk': row['played_krasnoyarsk'].strftime('%Y-%m-%d %H:%M:%S')
                if row.get('played_krasnoyarsk') else '—',
                'length': row['length'],
            }
            for row in queryset.values('file', 'played', 'played_krasnoyarsk', 'length')
        ]

        return JsonResponse({'count': len(results), 'results': results})

    # =========================================================================
    # ОСНОВНЫЕ НАСТРОЙКИ
    # =========================================================================

    list_display = (
        "id_short",
        "name",
        "owner_name",
        "timezone",
        "active_status_display",
        "status_display",
        "code1c",
        "brand_name",
        "legal_entity_name",
        "tenants_count_display",
        "id_rasb",
        "for_web"
    )

    inlines = [DiscountRuleInline]
    list_display_links = ("name",)

    search_fields = (
        "name",
        "code1c",
        "article",
        "id_rasb",
        "brand__name",
        "id"
    )

    list_filter = ("is_active", "timezone", "brand", "contentType")
    show_full_result_count = True
    list_per_page = 50

    autocomplete_fields = ['owner', 'brand', 'legalEntity', 'responsible_radio']
    raw_id_fields = ('owner', 'brand', 'legalEntity')

    # =========================================================================
    # ОПТИМИЗИРОВАННЫЙ QUERYSET С КЕШИРОВАНИЕМ ID
    # =========================================================================

    def get_queryset(self, request):
        """
        Оптимизированный запрос для списка номенклатур с кешированием ID.

        Кеширование ID вместо всего queryset для экономии памяти.
        """
        cache_key = f"nomenclature_admin_qs_{request.user.id}"
        cached_ids = cache.get(cache_key)

        if cached_ids is not None:
            return (
                Nomenclature.objects
                .filter(id__in=cached_ids)
                .select_related(
                    "owner", "availability", "brand", "legalEntity",
                    "responsible_radio", "responsible_ad",
                    "responsible_technic", "responsible_technic_on_address",
                    "responsible_placement_marketing", "typeOfPlace",
                )
                .prefetch_related(
                    "tenants",
                    Prefetch(
                        "images",
                        queryset=NomenclatureImage.objects.filter(type="exterior")[:1],
                        to_attr="prefetched_exterior"
                    ),
                    Prefetch(
                        "discount_rules",
                        queryset=DiscountRule.objects.all(),
                        to_attr="prefetched_discount_rules"
                    ),
                )
                .annotate(
                    tenants_count=Count("tenants", distinct=True),
                )
            )

        queryset = (
            Nomenclature.objects
            .select_related(
                "owner", "availability", "brand", "legalEntity",
                "responsible_radio", "responsible_ad",
                "responsible_technic", "responsible_technic_on_address",
                "responsible_placement_marketing", "typeOfPlace",
            )
            .prefetch_related(
                "tenants",
                Prefetch(
                    "images",
                    queryset=NomenclatureImage.objects.filter(type="exterior")[:1],
                    to_attr="prefetched_exterior"
                ),
                Prefetch(
                    "discount_rules",
                    queryset=DiscountRule.objects.all(),
                    to_attr="prefetched_discount_rules"
                ),
            )
            .annotate(
                tenants_count=Count("tenants", distinct=True),
            )
            .only(
                'id', 'name', 'timezone', 'is_active', 'code1c', 'article',
                'id_rasb', 'for_web',
                'owner__email', 'owner__first_name', 'owner__last_name',
                'availability__status', 'availability__last_answer_date',
                'brand__name', 'brand__id',
                'legalEntity__first_name', 'legalEntity__middle_name',
                'legalEntity__last_name', 'legalEntity__keyword',
                'responsible_radio__email', 'responsible_radio__first_name',
                'responsible_radio__last_name',
                'responsible_ad__email', 'responsible_ad__first_name',
                'responsible_ad__last_name',
                'responsible_technic__email', 'responsible_technic__first_name',
                'responsible_technic__last_name',
                'responsible_technic_on_address__email',
                'responsible_technic_on_address__first_name',
                'responsible_technic_on_address__last_name',
                'responsible_placement_marketing__email',
                'responsible_placement_marketing__first_name',
                'responsible_placement_marketing__last_name',
                'typeOfPlace__name', 'typeOfPlace__abbreviation',
            )
        )

        ids = list(queryset.values_list('id', flat=True))
        cache.set(cache_key, ids, 300)

        return queryset

    def get_search_results(self, request, queryset, search_term):
        """
        Оптимизированный поиск для админки без search_vector.
        """
        if not search_term:
            return queryset, False

        queryset = queryset.filter(
            Q(name__icontains=search_term) |
            Q(code1c__icontains=search_term) |
            Q(article__icontains=search_term) |
            Q(id_rasb__icontains=search_term) |
            Q(brand__name__icontains=search_term) |
            Q(id__icontains=search_term)
        ).distinct()

        return queryset, False

    # =========================================================================
    # ОПТИМИЗИРОВАННОЕ ПОЛУЧЕНИЕ ОБЪЕКТА
    # =========================================================================

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)

        if obj:
            cache_key = f"nomenclature_obj_full_{obj.pk}"
            cached = cache.get(cache_key)

            if not cached:
                prefetch_related_objects(
                    [obj],
                    'owner', 'brand', 'legalEntity',
                    'responsible_radio', 'responsible_ad',
                    'responsible_technic', 'responsible_technic_on_address',
                    'responsible_placement_marketing',
                    'availability', 'tenants',
                    'nomenclature_tenants',
                    'nomenclature_tenants__tenant',
                    'nomenclature_tenants__brand',
                    Prefetch(
                        'images',
                        queryset=NomenclatureImage.objects.order_by('-created')[:5],
                        to_attr='prefetched_images'
                    ),
                    Prefetch(
                        'discount_rules',
                        queryset=DiscountRule.objects.all().order_by('days_from'),
                        to_attr='prefetched_discount_rules'
                    ),
                )
                cache.set(cache_key, True, 300)

        return obj

    def get_form(self, request, obj=None, **kwargs):
        if obj and not hasattr(obj, '_prefetched_objects_cache'):
            obj = self.get_object(request, obj.pk)
        return super().get_form(request, obj, **kwargs)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and hasattr(obj, '_prefetched_objects_cache'):
            context['cached_fields'] = list(obj._prefetched_objects_cache.keys())
        return super().render_change_form(request, context, add, change, form_url, obj)

    # =========================================================================
    # ПОЛЯ ДЛЯ LIST_DISPLAY
    # =========================================================================

    @admin.display(description="ID", ordering="id")
    def id_short(self, obj):
        return str(obj.id)[:8] + "..."

    @admin.display(description="Владелец", ordering="owner__email")
    def owner_name(self, obj):
        if not obj.owner:
            return "-"
        if hasattr(obj.owner, 'full_name') and obj.owner.full_name:
            return obj.owner.full_name
        elif obj.owner.email:
            return obj.owner.email
        return f"ID:{str(obj.owner.id)[:8]}"

    @admin.display(description="Активность", ordering="is_active")
    def active_status_display(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                "✓ Активна"
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">{}</span>',
            "✗ Неактивна"
        )

    @admin.display(description="Статус", ordering="availability__status")
    def status_display(self, obj):
        try:
            status_code = obj.availability.status
            status_text = STATUSES.get(status_code, "Неизвестно")
            colors = {0: "green", 1: "orange", 2: "red"}
            color = colors.get(status_code, "gray")
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color,
                status_text
            )
        except (AttributeError, KeyError):
            return "Нет данных"

    @admin.display(description="Бренд", ordering="brand__name")
    def brand_name(self, obj):
        return obj.brand.name if obj.brand else "-"

    @admin.display(description="Юр.лицо", ordering="legalEntity__name")
    def legal_entity_name(self, obj):
        if not obj.legalEntity:
            return "-"
        if hasattr(obj.legalEntity, 'name'):
            return obj.legalEntity.name
        return f"ID:{str(obj.legalEntity.id)[:8]}"

    @admin.display(description="Арендаторы", ordering="tenants_count")
    def tenants_count_display(self, obj):
        count = getattr(obj, 'tenants_count', 0)
        if count > 0:
            url = f"/admin/nomenclatures/nomenclature/{obj.id}/change/"
            return format_html(
                '<a href="{}">{}</a>',
                url,
                f"{count} шт."
            )
        return "0"

    # =========================================================================
    # ДЕЙСТВИЯ
    # =========================================================================

    actions = ['activate', 'deactivate', 'clear_cache']

    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано {updated} номенклатур')
        cache.delete_pattern("nomenclature_admin_qs_*")

    activate.short_description = "Активировать выбранные"

    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано {updated} номенклатур')
        cache.delete_pattern("nomenclature_admin_qs_*")

    deactivate.short_description = "Деактивировать выбранные"

    def clear_cache(self, request, queryset):
        cache.delete_pattern("nomenclature_admin_qs_*")
        self.message_user(request, 'Кэш очищен')

    clear_cache.short_description = "Очистить кэш"


@admin.register(NomenclatureTenant)
class NomenclatureTenantAdmin(admin.ModelAdmin):
    list_display = ("nomenclature_name", "tenant", "brand", "floor", "atm")
    search_fields = ("floor",)
    list_filter = ("atm", "brand", "floor")
    autocomplete_fields = ("nomenclature", "tenant", "brand")
    show_full_result_count = True
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "nomenclature", "tenant", "brand",
        )

    @admin.display(description="Номенклатура", ordering="nomenclature__name")
    def nomenclature_name(self, obj):
        return obj.nomenclature.name if obj.nomenclature else "-"

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False

        queryset = queryset.filter(
            Q(nomenclature__brand__name__icontains=search_term) |
            Q(floor__icontains=search_term) |
            Q(nomenclature__name__icontains=search_term) |
            Q(nomenclature__code1c__icontains=search_term) |
            Q(nomenclature__article__icontains=search_term) |
            Q(nomenclature__id_rasb__icontains=search_term) |
            Q(brand__name__icontains=search_term)
        ).distinct()

        return queryset, False


@admin.register(TypeOfPlace)
class TypeOfPlaceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "abbreviation", "code1c", "is_mall", "is_active")
    list_filter = ("is_mall", "is_active")
    search_fields = ("name", "abbreviation", "code1c")
    show_full_result_count = True

    def get_queryset(self, request):
        return TypeOfPlace.objects.all()


@admin.register(NomenclatureAvailability)
class NomenclatureAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("client_name", "last_answer_date", "status_display")
    list_filter = ("status",)
    search_fields = ("client__name", "client__code1c")
    show_full_result_count = True
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
            color,
            status_text
        )


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("client_name", "change_time", "status_display")
    list_filter = ("status", "change_time")
    search_fields = ("client__name",)
    show_full_result_count = True
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
    list_display = ("id_short", "nomenclature_name", "type", "created", "hash_short")
    list_filter = ("type", "created")
    search_fields = ("nomenclature__name", "hash")
    show_full_result_count = True
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
    list_display = ("nomenclature_name", "address_short")
    search_fields = (
        "nomenclature__name",
        "address__city__name",
        "address__street__name",
        "address__house__number"
    )
    show_full_result_count = True
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "nomenclature", "address", "address__city",
            "address__street", "address__house", "address__building"
        ).only(
            'nomenclature__name', 'nomenclature__id',
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


@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    list_display = (
        "nomenclature_name", "days_from", "days_to",
        "coefficient", "discount_percent"
    )
    list_filter = ("nomenclature",)
    search_fields = ("nomenclature__name", "nomenclature__code1c")
    list_per_page = 50
    raw_id_fields = ("nomenclature",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("nomenclature").only(
            "id", "days_from", "days_to", "coefficient",
            "nomenclature__name", "nomenclature__id"
        )

    @admin.display(description="Номенклатура", ordering="nomenclature__name")
    def nomenclature_name(self, obj):
        return obj.nomenclature.name if obj.nomenclature else "-"

    @admin.display(description="Скидка")
    def discount_percent(self, obj):
        percent = (1 - obj.coefficient) * 100
        if percent <= 0:
            return "—"
        color = "green" if percent >= 15 else "orange"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            f"{percent:.1f}"
        )


@receiver(post_save, sender=Nomenclature)
@receiver(post_delete, sender=Nomenclature)
def invalidate_nomenclature_cache(sender, **kwargs):
    cache.delete_pattern("nomenclature_admin_qs_*")
    if 'instance' in kwargs:
        cache.delete(f"nomenclature_obj_full_{kwargs['instance'].pk}")

# from django.contrib import admin
# from django.core.cache import cache
# from django.db.models import Prefetch, Count
# from django.db.models import prefetch_related_objects
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from django.utils.html import format_html
# from django.http import JsonResponse
# from django.utils.dateparse import parse_date
# from django.contrib.admin.views.decorators import staff_member_required
# from ch_statistic.models import MusicStat
# from nomenclatures.models import (
#     Nomenclature,
#     NomenclatureAvailability,
#     StatusHistory,
#     STATUSES,
#     NomenclatureImage,
#     NomenclatureAddress,
#     TypeOfPlace,
#     NomenclatureTenant, DiscountRule
# )
# class DiscountRuleInline(admin.TabularInline):
#     model = DiscountRule
#     extra = 1
#     fields = ("days_from", "days_to", "coefficient")
#     ordering = ("days_from",)

# @admin.register(Nomenclature)
# class NomenclatureAdmin(admin.ModelAdmin):
#     """Номенклатура — полностью оптимизированная версия с сохранением подсчета"""

#     def get_urls(self):
#         from django.urls import path
#         urls = super().get_urls()
#         custom = [
#             path(
#                 '<uuid:object_id>/music-stat/',
#                 self.admin_site.admin_view(self.music_stat_view),
#                 name='nomenclature_music_stat',
#             ),
#         ]
#         return custom + urls

#     def music_stat_view(self, request, object_id):
#         date_from = request.GET.get('date_from')
#         date_to = request.GET.get('date_to')

#         if not date_from or not date_to:
#             return JsonResponse({'error': 'Укажите date_from и date_to'}, status=400)

#         parsed_from = parse_date(date_from)
#         parsed_to = parse_date(date_to)

#         if not parsed_from or not parsed_to:
#             return JsonResponse({'error': 'Неверный формат даты'}, status=400)

#         qs = (
#             MusicStat.objects
#             .filter(
#                 client=str(object_id),
#                 played__date__gte=parsed_from,
#                 played__date__lte=parsed_to,
#             )
#             .order_by('-played')
#             .values('file', 'played', 'length')[:200]  # лимит 200 записей
#         )

#         results = [
#             {
#                 'file': row['file'],
#                 'played': row['played'].strftime('%Y-%m-%d %H:%M:%S'),
#                 'played_krasnoyarsk': row['played_krasnoyarsk'].strftime('%Y-%m-%d %H:%M:%S') if row[
#                     'played_krasnoyarsk'] else '—',
#                 'length': row['length'],
#             }
#             for row in qs.values('file', 'played', 'played_krasnoyarsk', 'length')
#         ]

#         return JsonResponse({'count': len(results), 'results': results})

#     # ========== ОСНОВНЫЕ НАСТРОЙКИ ==========
#     list_display = (
#         "id_short",
#         "name",
#         "owner_name",
#         "timezone",
#         "active_status_display",
#         "status_display",
#         "code1c",
#         "brand_name",
#         "legal_entity_name",
#         "tenants_count_display",
#         "id_rasb",
#         "for_web"
#     )
#     inlines = [DiscountRuleInline]
#     list_display_links = ("name",)

#     # Исправляем search_fields - убираем brand.name, оставляем search_vector
#     search_fields = (
#         "name",
#         "code1c",
#         "article",
#         "id_rasb",
#         "search_vector",  # Добавляем новое поле
#         "brand__name",  # Правильный синтаксис для связанных полей
#     )

#     list_filter = ("is_active", "timezone", "brand", "contentType")
#     show_full_result_count = True
#     list_per_page = 50
#     autocomplete_fields = ['owner', 'brand', 'legalEntity', 'responsible_radio']
#     raw_id_fields = ('owner', 'brand', 'legalEntity')

#     # ========== ОПТИМИЗАЦИЯ QUERYSET ДЛЯ СПИСКА ==========
#     def get_queryset(self, request):
#         cache_key = f"nomenclature_admin_qs_{request.user.id}"
#         qs = cache.get(cache_key)

#         if not qs:
#             qs = Nomenclature.objects.all().select_related(
#                 "owner",
#                 "availability",
#                 "brand",
#                 "legalEntity",
#                 "responsible_radio",
#                 "responsible_ad",
#             ).prefetch_related(
#                 "tenants",
#                 Prefetch(
#                     "images",
#                     queryset=NomenclatureImage.objects.filter(type="exterior")[:1],
#                     to_attr="prefetched_exterior"
#                 ),
#             ).annotate(
#                 tenants_count=Count("tenants", distinct=True),
#             ).only(
#                 'id', 'name', 'timezone', 'is_active', 'code1c', 'article',
#                 'owner__email', 'owner__first_name', 'owner__last_name',
#                 'availability__status', 'availability__last_answer_date',
#                 'brand__name',
#                 'legalEntity__first_name', 'legalEntity__middle_name',
#                 'legalEntity__last_name', 'legalEntity__keyword',
#                 'responsible_radio__email', 'responsible_radio__first_name', 'responsible_radio__last_name',
#                 'responsible_ad__email', 'responsible_ad__first_name', 'responsible_ad__last_name',
#             )

#             cache.set(cache_key, qs, 300)

#         return qs

#     # ========== ОПТИМИЗАЦИЯ ФОРМЫ РЕДАКТИРОВАНИЯ ==========
#     def get_object(self, request, object_id, from_field=None):
#         obj = super().get_object(request, object_id, from_field)

#         if obj:
#             cache_key = f"nomenclature_obj_full_{obj.pk}"
#             cached = cache.get(cache_key)

#             if not cached:
#                 prefetch_related_objects(
#                     [obj],
#                     'owner', 'brand', 'legalEntity',
#                     'responsible_radio', 'responsible_ad',
#                     'responsible_technic', 'responsible_technic_on_address',
#                     'responsible_placement_marketing',
#                     'availability',
#                     'tenants',
#                     Prefetch(
#                         'images',
#                         queryset=NomenclatureImage.objects.order_by('-created')[:5],
#                         to_attr='prefetched_images'
#                     ),
#                 )
#                 cache.set(cache_key, True, 300)

#         return obj

#     def get_form(self, request, obj=None, **kwargs):
#         form = super().get_form(request, obj, **kwargs)
#         if obj:
#             if not hasattr(obj, '_prefetched_objects_cache'):
#                 obj = self.get_object(request, obj.pk)
#         return form

#     def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
#         if obj and hasattr(obj, '_prefetched_objects_cache'):
#             context['cached_fields'] = list(obj._prefetched_objects_cache.keys())
#         return super().render_change_form(request, context, add, change, form_url, obj)

#     # ========== КАСТОМНЫЕ ПОЛЯ ДЛЯ LIST_DISPLAY ==========

#     @admin.display(description="ID", ordering="id")
#     def id_short(self, obj):
#         return str(obj.id)[:8] + "..."

#     @admin.display(description="Владелец", ordering="owner__email")
#     def owner_name(self, obj):
#         if not obj.owner:
#             return "-"
#         if hasattr(obj.owner, 'full_name') and obj.owner.full_name:
#             return obj.owner.full_name
#         elif obj.owner.email:
#             return obj.owner.email
#         else:
#             return f"ID:{str(obj.owner.id)[:8]}"

#     @admin.display(description="Активность", ordering="is_active")
#     def active_status_display(self, obj):
#         """Статус активности с цветовой индикацией"""
#         if obj.is_active:
#             return format_html('<span style="color: green; font-weight: bold;">{}</span>', "✓ Активна")
#         else:
#             return format_html('<span style="color: red; font-weight: bold;">{}</span>', "✗ Неактивна")

#     @admin.display(description="Статус", ordering="availability__status")
#     def status_display(self, obj):
#         """Статус доступности с цветовой индикацией"""
#         try:
#             status_code = obj.availability.status
#             status_text = STATUSES.get(obj.availability.status, "Неизвестно")
#             colors = {0: "green", 1: "orange", 2: "red"}
#             color = colors.get(status_code, "gray")
#             return format_html(
#                 '<span style="color: {}; font-weight: bold;">{}</span>',
#                 color, status_text
#             )
#         except (AttributeError, KeyError):
#             return "Нет данных"

#     @admin.display(description="Бренд", ordering="brand__name")
#     def brand_name(self, obj):
#         return obj.brand.name if obj.brand else "-"

#     @admin.display(description="Юр.лицо", ordering="legalEntity__name")
#     def legal_entity_name(self, obj):
#         if not obj.legalEntity:
#             return "-"
#         if hasattr(obj.legalEntity, 'name'):
#             return obj.legalEntity.name
#         else:
#             return f"ID:{str(obj.legalEntity.id)[:8]}"

#     @admin.display(description="Арендаторы")
#     def tenants_count_display(self, obj):
#         count = getattr(obj, 'tenants_count', 0)
#         if count > 0:
#             url = f"/admin/nomenclatures/nomenclature/{obj.id}/change/"
#             return format_html('<a href="{}">{}</a>', url, f"{count} шт.")
#         return "0"

#     # ========== ДЕЙСТВИЯ ==========
#     actions = ['activate', 'deactivate', 'clear_cache']

#     def activate(self, request, queryset):
#         updated = queryset.update(is_active=True)
#         self.message_user(request, f'Активировано {updated} номенклатур')
#         cache.delete_pattern("nomenclature_admin_qs_*")

#     activate.short_description = "Активировать выбранные"

#     def deactivate(self, request, queryset):
#         updated = queryset.update(is_active=False)
#         self.message_user(request, f'Деактивировано {updated} номенклатур')
#         cache.delete_pattern("nomenclature_admin_qs_*")

#     deactivate.short_description = "Деактивировать выбранные"

#     def clear_cache(self, request, queryset):
#         cache.delete_pattern("nomenclature_admin_qs_*")
#         self.message_user(request, 'Кэш очищен')

#     clear_cache.short_description = "Очистить кэш"


# from django.contrib import admin
# from django.db.models import Q


# @admin.register(NomenclatureTenant)
# class NomenclatureTenantAdmin(admin.ModelAdmin):
#     list_display = ("nomenclature_name", "tenant", "brand", "floor", "atm")
#     search_fields = ("floor",)
#     list_filter = ("atm", "brand", "floor")
#     autocomplete_fields = ("nomenclature", "tenant", "brand")
#     show_full_result_count = True
#     list_per_page = 50

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related(
#             "nomenclature",
#             "tenant",
#             "brand",
#         )

#     @admin.display(description="Номенклатура", ordering="nomenclature__name")
#     def nomenclature_name(self, obj):
#         return obj.nomenclature.name if obj.nomenclature else "-"

#     def get_search_results(self, request, queryset, search_term):
#         if not search_term:
#             return queryset, False

#         queryset = queryset.filter(
#             Q(nomenclature__brand__name__icontains=search_term)
#             | Q(floor__icontains=search_term)
#             | Q(nomenclature__name__icontains=search_term)
#             | Q(nomenclature__code1c__icontains=search_term)
#             | Q(nomenclature__article__icontains=search_term)
#             | Q(nomenclature__id_rasb__icontains=search_term)
#             | Q(brand__name__icontains=search_term)
#         ).distinct()

#         return queryset, False


# @admin.register(TypeOfPlace)
# class TypeOfPlaceAdmin(admin.ModelAdmin):
#     list_display = ("id", "name", "abbreviation", "code1c", "is_mall", "is_active")
#     list_filter = ("is_mall", "is_active")
#     search_fields = ("name", "abbreviation", "code1c")
#     show_full_result_count = True

#     def get_queryset(self, request):
#         return TypeOfPlace.objects.all()


# @admin.register(NomenclatureAvailability)
# class NomenclatureAvailabilityAdmin(admin.ModelAdmin):
#     list_display = ("client_name", "last_answer_date", "status_display")
#     list_filter = ("status",)
#     search_fields = ("client__name", "client__code1c")
#     show_full_result_count = True
#     raw_id_fields = ("client",)

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related("client").only(
#             'client__name', 'client__id',
#             'last_answer_date', 'status'
#         )

#     @admin.display(description="Номенклатура", ordering="client__name")
#     def client_name(self, obj):
#         return obj.client.name if obj.client else "-"

#     @admin.display(description="Статус")
#     def status_display(self, obj):
#         status_text = STATUSES.get(obj.status, "Неизвестно")
#         colors = {0: "green", 1: "orange", 2: "red"}
#         color = colors.get(obj.status, "gray")
#         return format_html('<span style="color: {};">{}</span>', color, status_text)


# @admin.register(StatusHistory)
# class StatusHistoryAdmin(admin.ModelAdmin):
#     list_display = ("client_name", "change_time", "status_display")
#     list_filter = ("status", "change_time")
#     search_fields = ("client__name",)
#     show_full_result_count = True
#     raw_id_fields = ("client",)
#     list_per_page = 100

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related("client").only(
#             'client__name', 'client__id',
#             'change_time', 'status'
#         )

#     @admin.display(description="Номенклатура", ordering="client__name")
#     def client_name(self, obj):
#         return obj.client.name if obj.client else "-"

#     @admin.display(description="Статус")
#     def status_display(self, obj):
#         return STATUSES.get(obj.status, "Неизвестно")


# @admin.register(NomenclatureImage)
# class NomenclatureImageAdmin(admin.ModelAdmin):
#     list_display = ("id_short", "nomenclature_name", "type", "created", "hash_short")
#     list_filter = ("type", "created")
#     search_fields = ("nomenclature__name", "hash")
#     show_full_result_count = True
#     raw_id_fields = ("nomenclature",)
#     list_per_page = 50

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related("nomenclature").only(
#             'id', 'type', 'created', 'hash',
#             'nomenclature__name', 'nomenclature__id'
#         )

#     @admin.display(description="ID")
#     def id_short(self, obj):
#         return str(obj.id)[:8] + "..."

#     @admin.display(description="Номенклатура", ordering="nomenclature__name")
#     def nomenclature_name(self, obj):
#         return obj.nomenclature.name if obj.nomenclature else "-"

#     @admin.display(description="Хэш")
#     def hash_short(self, obj):
#         return f"{obj.hash[:8]}..." if obj.hash else "-"


# @admin.register(NomenclatureAddress)
# class NomenclatureAddressAdmin(admin.ModelAdmin):
#     list_display = ("nomenclature_name", "address_short")
#     search_fields = ("nomenclature__name", "address__city__name", "address__street__name", "address__house__number")
#     show_full_result_count = True
#     list_per_page = 50

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related(
#             "nomenclature",
#             "address",
#             "address__city",
#             "address__street",
#             "address__house",
#             "address__building"
#         ).only(
#             'nomenclature__name', 'nomenclature__id',
#             'address__id',
#             'address__city__name',
#             'address__street__name',
#             'address__house__number',
#             'address__building__number'
#         )

#     @admin.display(description="Номенклатура", ordering="nomenclature__name")
#     def nomenclature_name(self, obj):
#         return obj.nomenclature.name if obj.nomenclature else "-"

#     @admin.display(description="Адрес")
#     def address_short(self, obj):
#         if not obj.address:
#             return "-"
#         return str(obj.address)[:50]


# @admin.register(DiscountRule)
# class DiscountRuleAdmin(admin.ModelAdmin):
#     list_display = ("nomenclature_name", "days_from", "days_to", "coefficient", "discount_percent")
#     list_filter = ("nomenclature",)
#     search_fields = ("nomenclature__name", "nomenclature__code1c")
#     list_per_page = 50
#     raw_id_fields = ("nomenclature",)

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related("nomenclature").only(
#             "id", "days_from", "days_to", "coefficient",
#             "nomenclature__name", "nomenclature__id"
#         )

#     @admin.display(description="Номенклатура", ordering="nomenclature__name")
#     def nomenclature_name(self, obj):
#         return obj.nomenclature.name if obj.nomenclature else "-"

#     @admin.display(description="Скидка")
#     def discount_percent(self, obj):
#         percent = (1 - obj.coefficient) * 100
#         if percent <= 0:
#             return "—"
#         color = "green" if percent >= 15 else "orange"
#         return format_html(
#             '<span style="color: {}; font-weight: bold;">{}%</span>',
#             color, f"{percent:.1f}"
#         )

# # ========== ИНВАЛИДАЦИЯ КЭША ==========
# @receiver(post_save, sender=Nomenclature)
# @receiver(post_delete, sender=Nomenclature)
# def invalidate_nomenclature_cache(sender, **kwargs):
#     cache.delete_pattern("nomenclature_admin_qs_*")
#     if 'instance' in kwargs:
#         cache.delete(f"nomenclature_obj_full_{kwargs['instance'].pk}")
