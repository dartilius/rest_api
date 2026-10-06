"""
Административный интерфейс для модели Nomenclature.

ОПТИМИЗАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ:
───────────────────────────────────────────────────────────────────────────────
1. Использование select_related для всех FK связей (1 запрос вместо N)
2. Использование prefetch_related для всех M2M связей (1 запрос вместо N)
3. Пагинация без материализации всего каталога и без лишних полных COUNT
4. Оптимизация list_display для исключения отдельных запросов к БД
5. Поиск без search_vector для ускорения админки
6. Устранение дублирующихся запросов в get_form и render_change_form
"""

from datetime import UTC, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.widgets import AutocompleteSelect, RelatedFieldWidgetWrapper
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch, Count, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.utils.html import format_html

from brands.models import Brand
from ch_statistic.models import MusicStat
from nomenclatures.models import (
    Nomenclature,
    NomenclatureAvailability,
    StatusHistory,
    STATUSES,
    NomenclatureImage,
    NomenclatureVideo,
    NomenclatureAddress,
    TypeOfPlace,
    NomenclatureTenant,
    DiscountRule,
    StationInstallation,
)
from nomenclatures.tasks import maintenance_mode_task
from users.models import CustomUser


class SelectedLabelAutocompleteSelect(AutocompleteSelect):
    """Render already loaded selected labels without one SQL query per field."""

    def __init__(self, *args, selected_labels=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_labels = selected_labels or {}

    def optgroups(self, name, value, attrs=None):
        selected_choices = {
            str(item) for item in value if str(item) not in self.choices.field.empty_values
        }
        if not selected_choices <= self.selected_labels.keys():
            # Preserve Django's normal behavior for an invalid POSTed value.
            return super().optgroups(name, value, attrs)

        default = (None, [], 0)
        if not self.is_required and not self.allow_multiple_selected:
            default[1].append(self.create_option(name, "", "", False, 0))
        for index, option_value in enumerate(value, start=len(default[1])):
            option_key = str(option_value)
            if option_key not in selected_choices:
                continue
            default[1].append(
                self.create_option(
                    name,
                    option_value,
                    self.selected_labels[option_key],
                    True,
                    index,
                )
            )
        return [default]


class DiscountRuleInline(admin.TabularInline):
    """
    Inline-форма для правил скидок в административной панели.
    """

    model = DiscountRule
    extra = 1
    fields = ("days_from", "days_to", "coefficient")
    ordering = ("days_from",)


class StationInstallationInline(admin.TabularInline):
    """История автоматических привязок Player в карточке точки вещания."""

    model = StationInstallation
    extra = 0
    can_delete = False
    fields = ("id", "created_by", "is_active", "token_hash", "created_at", "rotated_at")
    readonly_fields = fields
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Nomenclature.
    """

    change_form_template = "nomenclatures/nomenclature/change_form.html"
    show_facets = admin.ShowFacets.NEVER

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom = [
            path(
                "<uuid:object_id>/music-stat/",
                self.admin_site.admin_view(self.music_stat_view),
                name="nomenclature_music_stat",
            ),
            path(
                "<uuid:object_id>/maintenance/",
                self.admin_site.admin_view(self.maintenance_mode_view),
                name="nomenclature_maintenance",
            ),
        ]
        return custom + urls

    def maintenance_mode_view(self, request, object_id):
        """Queue a service-mode command from the station card in Django Admin."""
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        nomenclature = self.get_object(request, object_id)
        if nomenclature is None:
            return redirect("admin:nomenclatures_nomenclature_changelist")
        if not self.has_change_permission(request, nomenclature):
            raise PermissionDenied

        enabled_value = request.POST.get("enabled")
        if enabled_value not in {"true", "false"}:
            self.message_user(
                request,
                "Выберите состояние сервисного режима.",
                level=messages.ERROR,
            )
        else:
            enabled = enabled_value == "true"
            reason = request.POST.get("reason", "").strip()
            if enabled and not reason:
                self.message_user(
                    request,
                    "Для входа в сервисный режим укажите причину.",
                    level=messages.ERROR,
                )
            else:
                maintenance_mode_task.delay(
                    str(nomenclature.pk),
                    enabled,
                    reason,
                    str(request.user.pk),
                )
                state = "включение" if enabled else "выключение"
                self.message_user(
                    request,
                    f"Команда на {state} сервисного режима поставлена в очередь.",
                    level=messages.SUCCESS,
                )

        return redirect(
            reverse("admin:nomenclatures_nomenclature_change", args=[nomenclature.pk])
        )

    def music_stat_view(self, request, object_id):
        if request.method != "GET":
            return HttpResponseNotAllowed(["GET"])
        nomenclature = self.get_object(request, object_id)
        if nomenclature is None:
            return JsonResponse({"error": "Номенклатура не найдена"}, status=404)
        if not self.has_view_permission(request, nomenclature):
            raise PermissionDenied

        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        if not date_from or not date_to:
            return JsonResponse({"error": "Укажите date_from и date_to"}, status=400)

        try:
            parsed_from = parse_date(date_from)
            parsed_to = parse_date(date_to)
        except ValueError:
            return JsonResponse({"error": "Неверный формат даты"}, status=400)

        if not parsed_from or not parsed_to:
            return JsonResponse({"error": "Неверный формат даты"}, status=400)
        if parsed_from > parsed_to:
            return JsonResponse({"error": "Начало периода позже его окончания"}, status=400)

        queryset = (
            MusicStat.objects.filter(
                client=str(object_id),
                played__gte=datetime.combine(parsed_from, time.min, tzinfo=UTC),
                played__lte=datetime.combine(parsed_to, time.max, tzinfo=UTC),
            )
            .order_by("-played")
            .values("file", "played", "length")[:200]
        )

        results = []
        for row in queryset:
            played = row["played"]
            if played.tzinfo is None:
                played = played.replace(tzinfo=UTC)
            results.append({
                "file": row["file"],
                "played": row["played"].strftime("%Y-%m-%d %H:%M:%S"),
                "played_krasnoyarsk": played.astimezone(
                    ZoneInfo("Asia/Krasnoyarsk")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "length": row["length"],
            })

        return JsonResponse({"count": len(results), "results": results})

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
        "for_web",
        "typeOfPlace__abbreviation",
    )

    inlines = [DiscountRuleInline, StationInstallationInline]
    list_display_links = ("name",)

    search_fields = ("name", "code1c", "article", "id_rasb", "brand__name", "id")

    list_filter = (
        "version",
        "is_active",
        "timezone",
        "brand",
        "contentType",
        "typeOfPlace__abbreviation",
        "for_web",
    )
    # Пагинатор уже считает отфильтрованный queryset. Полный count всех записей
    # дублирует тяжёлый GROUP BY по арендаторам на каждой загрузке списка.
    show_full_result_count = False
    list_per_page = 50

    autocomplete_fields = [
        "owner",
        "brand",
        "legalEntity",
        "responsible_radio",
        "responsible_ad",
        "responsible_technic",
        "responsible_technic_on_address",
        "responsible_placement_marketing",
        "typeOfPlace",
    ]
    responsible_fields = (
        "responsible_radio",
        "responsible_ad",
        "responsible_technic",
        "responsible_technic_on_address",
        "responsible_placement_marketing",
    )
    readonly_fields = ("hw_info", "runtime_state")

    # =========================================================================
    # ОПТИМИЗИРОВАННЫЙ QUERYSET ДЛЯ СПИСКА
    # =========================================================================

    def get_queryset(self, request):
        """Load display relations without deferring fields needed by the edit form."""
        # APIBaseObjectModel's default manager is `active`. Admin must include
        # inactive stations too; only an explicit list filter may exclude them.
        queryset = self.model.objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            queryset = queryset.order_by(*ordering)
        if getattr(getattr(request, "resolver_match", None), "url_name", None) == "autocomplete":
            # Autocomplete renders only the station name, not its list columns.
            return queryset.only("id", "name").order_by("name", "pk")
        tenant_counts = (
            NomenclatureTenant.objects.filter(nomenclature_id=OuterRef("pk"))
            .order_by()
            .values("nomenclature_id")
            .annotate(total=Count("tenant_id", distinct=True))
            .values("total")
        )
        return (
            queryset
            .select_related("owner", "availability", "brand", "legalEntity", "typeOfPlace")
            .prefetch_related(
                Prefetch(
                    "legalEntity__brands",
                    queryset=Brand.objects.only("id", "name"),
                    to_attr="_prefetched_brands",
                ),
            )
            .annotate(tenants_count=Coalesce(Subquery(tenant_counts), 0))
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            return form

        selected_user_ids = {
            str(user_id)
            for field_name in self.responsible_fields
            if (user_id := getattr(obj, f"{field_name}_id")) is not None
        }
        if not selected_user_ids:
            return form

        cache = getattr(request, "_nomenclature_responsible_label_cache", {})
        cache_key = frozenset(selected_user_ids)
        selected_labels = cache.get(cache_key)
        if selected_labels is None:
            selected_labels = {
                str(user.pk): str(user)
                for user in CustomUser.objects.filter(pk__in=selected_user_ids)
                .only("id", "last_name", "first_name", "middle_name")
                .order_by()
            }
            cache[cache_key] = selected_labels
            request._nomenclature_responsible_label_cache = cache
        for field_name in self.responsible_fields:
            field = form.base_fields.get(field_name)
            if field is None:
                continue
            wrapper = field.widget
            widget = wrapper.widget if isinstance(wrapper, RelatedFieldWidgetWrapper) else wrapper
            if not isinstance(widget, AutocompleteSelect):
                continue
            cached_widget = SelectedLabelAutocompleteSelect(
                widget.field,
                widget.admin_site,
                attrs=widget.attrs,
                choices=widget.choices,
                using=widget.db,
                selected_labels=selected_labels,
            )
            if isinstance(wrapper, RelatedFieldWidgetWrapper):
                wrapper.widget = cached_widget
                wrapper.attrs = cached_widget.attrs
            else:
                field.widget = cached_widget
        return form

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False
        # All searched relations are FK: they cannot multiply the station rows.
        return queryset.filter(
            Q(name__icontains=search_term)
            | Q(code1c__icontains=search_term)
            | Q(article__icontains=search_term)
            | Q(id_rasb__icontains=search_term)
            | Q(brand__name__icontains=search_term)
            | Q(id__icontains=search_term)
        ), False

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
        full_name = obj.owner.full_name
        if full_name:
            return full_name
        if obj.owner.email:
            return obj.owner.email
        return f"ID:{str(obj.owner.id)[:8]}"

    @admin.display(description="Активность", ordering="is_active")
    def active_status_display(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>', "✓ Активна"
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">{}</span>', "✗ Неактивна"
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
                status_text,
            )
        except (AttributeError, KeyError):
            return "Нет данных"

    @admin.display(description="Бренд", ordering="brand__name")
    def brand_name(self, obj):
        return obj.brand.name if obj.brand else "-"

    @admin.display(description="Юр.лицо", ordering="legalEntity__keyword")
    def legal_entity_name(self, obj):
        if not obj.legalEntity:
            return "-"
        return obj.legalEntity.name or f"ID:{str(obj.legalEntity.id)[:8]}"

    @admin.display(description="Арендаторы", ordering="tenants_count")
    def tenants_count_display(self, obj):
        count = getattr(obj, "tenants_count", 0)
        if count > 0:
            url = reverse("admin:nomenclatures_nomenclature_change", args=[obj.pk])
            return format_html('<a href="{}">{}</a>', url, f"{count} шт.")
        return "0"

    # =========================================================================
    # ДЕЙСТВИЯ
    # =========================================================================

    actions = ["activate", "deactivate"]

    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано {updated} номенклатур")

    activate.short_description = "Активировать выбранные"

    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано {updated} номенклатур")

    deactivate.short_description = "Деактивировать выбранные"


@admin.register(NomenclatureTenant)
class NomenclatureTenantAdmin(admin.ModelAdmin):
    list_display = ("nomenclature_name", "tenant", "brand", "floor", "atm")
    search_fields = ("floor",)
    list_filter = ("atm", "brand", "floor")
    autocomplete_fields = ("nomenclature", "tenant", "brand")
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER
    list_per_page = 50

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "nomenclature",
                "tenant",
                "brand",
            )
            .prefetch_related(
                Prefetch(
                    "tenant__brands",
                    queryset=Brand.objects.only("id", "name"),
                    to_attr="_prefetched_brands",
                )
            )
        )

    @admin.display(description="Номенклатура", ordering="nomenclature__name")
    def nomenclature_name(self, obj):
        return obj.nomenclature.name if obj.nomenclature else "-"

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False

        queryset = queryset.filter(
            Q(nomenclature__brand__name__icontains=search_term)
            | Q(floor__icontains=search_term)
            | Q(nomenclature__name__icontains=search_term)
            | Q(nomenclature__code1c__icontains=search_term)
            | Q(nomenclature__article__icontains=search_term)
            | Q(nomenclature__id_rasb__icontains=search_term)
            | Q(brand__name__icontains=search_term)
        )

        return queryset, False


@admin.register(TypeOfPlace)
class TypeOfPlaceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "abbreviation", "code1c", "is_mall", "is_active")
    list_filter = ("is_mall", "is_active")
    search_fields = ("name", "abbreviation", "code1c")
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER

    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(NomenclatureAvailability)
class NomenclatureAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("client_name", "last_answer_date", "status_display")
    list_filter = ("status",)
    search_fields = ("client__name", "client__code1c")
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER
    autocomplete_fields = ("client",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("client")
            .only("client__name", "client__id", "last_answer_date", "status")
        )

    @admin.display(description="Номенклатура", ordering="client__name")
    def client_name(self, obj):
        return obj.client.name if obj.client else "-"

    @admin.display(description="Статус")
    def status_display(self, obj):
        status_text = STATUSES.get(obj.status, "Неизвестно")
        colors = {0: "green", 1: "orange", 2: "red"}
        color = colors.get(obj.status, "gray")
        return format_html('<span style="color: {};">{}</span>', color, status_text)


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("client_name", "change_time", "status_display")
    list_filter = ("status", "change_time")
    search_fields = ("client__name",)
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER
    autocomplete_fields = ("client",)
    list_per_page = 100

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("client")
            .only("client__name", "client__id", "change_time", "status")
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
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER
    autocomplete_fields = ("nomenclature",)
    list_per_page = 50

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("nomenclature")
            .only(
                "id",
                "type",
                "created",
                "hash",
                "source",
                "nomenclature__name",
                "nomenclature__id",
            )
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


@admin.register(NomenclatureVideo)
class NomenclatureVideoAdmin(NomenclatureImageAdmin):
    """Административный интерфейс для видеозаписей номенклатур."""


@admin.register(NomenclatureAddress)
class NomenclatureAddressAdmin(admin.ModelAdmin):
    list_display = ("nomenclature_name", "address_short")
    search_fields = (
        "nomenclature__name",
        "address__city__name",
        "address__street__name",
        "address__house__number",
    )
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER
    list_per_page = 50
    autocomplete_fields = ("nomenclature", "address")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "nomenclature",
                "address",
                "address__city",
                "address__city__locality_type",
                "address__street",
                "address__street__street_type",
                "address__house",
                "address__building",
                "address__region",
                "address__region__type_region",
                "address__administrative_unit",
            )
        )

    @admin.display(description="Номенклатура", ordering="nomenclature__name")
    def nomenclature_name(self, obj):
        return obj.nomenclature.name if obj.nomenclature else "-"

    @admin.display(description="Адрес")
    def address_short(self, obj):
        if not obj.address:
            return "-"
        return str(obj.address)[:50]


class DiscountStationFilter(admin.SimpleListFilter):
    """Filter by station UUID without loading the complete station directory."""

    title = "Номенклатура (UUID)"
    parameter_name = "station_uuid"
    template = "admin/nomenclatures/station_uuid_filter.html"

    def __init__(self, request, params, model, model_admin):
        self.query_parts = [
            (key, value)
            for key, values in request.GET.lists()
            if key not in (self.parameter_name, "p")
            for value in values
        ]
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        return ()

    def has_output(self):
        return True

    def choices(self, changelist):
        yield {
            "query_parts": self.query_parts,
            "value": self.value() or "",
            "reset_url": changelist.get_query_string(remove=[self.parameter_name]),
        }

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        try:
            station_id = UUID(value)
        except (ValueError, AttributeError):
            return queryset.none()
        return queryset.filter(nomenclature_id=station_id)


@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    list_display = (
        "nomenclature_name",
        "days_from",
        "days_to",
        "coefficient",
        "discount_percent",
    )
    list_filter = (DiscountStationFilter,)
    search_fields = ("nomenclature__name", "nomenclature__code1c")
    list_per_page = 50
    autocomplete_fields = ("nomenclature",)
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("nomenclature")
            .only(
                "id",
                "days_from",
                "days_to",
                "coefficient",
                "nomenclature__name",
                "nomenclature__id",
            )
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
            f"{percent:.1f}",
        )
