"""Административный интерфейс для контрагентов."""

from django.contrib import admin
from django.db.models import Count, Prefetch
from django.utils.html import format_html, format_html_join

from brands.models import Brand
from counterparties.models import (
    Counterparty,
    CounterpartyCategory,
    CounterpartyCategoryAssignment,
    CounterpartyContactInfo,
)


@admin.register(CounterpartyCategory)
class CounterpartyCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


class ContactInfoInline(admin.TabularInline):
    model = CounterpartyContactInfo
    extra = 1
    readonly_fields = ("id",)
    fields = ("type", "meaning", "vidtel", "vidmail", "ext", "basic", "comment")


class CounterpartyCategoryAssignmentInline(admin.TabularInline):
    model = CounterpartyCategoryAssignment
    extra = 1
    autocomplete_fields = ("category",)
    readonly_fields = ("assigned_at",)
    fields = ("category", "assigned_at")
    verbose_name = "Категория контрагента"
    verbose_name_plural = "Категории контрагентов"


@admin.register(Counterparty)
class CounterpartiesAdmin(admin.ModelAdmin):
    """Администрирование всех контрагентов, включая неактивные."""

    list_display = (
        "id",
        "name",
        "is_active",
        "code1c",
        "owned_count",
        "rented_count",
        "brands_count",
        "contact_persons_count",
    )
    search_fields = ("first_name", "middle_name", "last_name", "keyword")
    list_filter = ("is_active",)
    filter_horizontal = ("brands", "contact_persons")
    readonly_fields = ("show_owned", "show_rented", "code1c", "display_brands", "brands_count")
    inlines = [CounterpartyCategoryAssignmentInline, ContactInfoInline]
    list_per_page = 50
    show_full_result_count = False

    fieldsets = (
        ("Основная информация", {
            "fields": ("first_name", "middle_name", "last_name", "keyword", "opf", "code1c", "is_active"),
        }),
        ("Бренды", {"fields": ("display_brands", "brands_count")} ),
        ("Описание", {"fields": ("description",)}),
        ("Свои номенклатуры (legalEntity)", {"fields": ("show_owned",)}),
        ("Арендованные номенклатуры (tenants)", {"fields": ("show_rented",)}),
        ("Контактные лица", {"fields": ("contact_persons",)}),
    )

    def get_queryset(self, request):
        """Добавляет счётчики и бренды для свойства name без кеширования QuerySet."""
        return (
            Counterparty.objects
            .prefetch_related(
                Prefetch(
                    "brands",
                    queryset=Brand.objects.only("id", "name"),
                    to_attr="_prefetched_brands",
                ),
            )
            .annotate(
                owned_count=Count("owned_nomenclatures", distinct=True),
                rented_count=Count("rented_nomenclatures", distinct=True),
                brands_count=Count("brands", distinct=True),
                contact_persons_count=Count("contact_persons", distinct=True),
            )
            .only(
                "id", "first_name", "middle_name", "last_name", "keyword", "opf",
                "code1c", "is_active", "description", "additional_name",
            )
        )

    @admin.display(description="Своих номенклатур", ordering="owned_count")
    def owned_count(self, obj):
        return obj.owned_count

    @admin.display(description="Арендованных", ordering="rented_count")
    def rented_count(self, obj):
        return obj.rented_count

    @admin.display(description="Брендов", ordering="brands_count")
    def brands_count(self, obj):
        return obj.brands_count

    @admin.display(description="Контактных лиц", ordering="contact_persons_count")
    def contact_persons_count(self, obj):
        return obj.contact_persons_count

    @admin.display(description="Бренды КА")
    def display_brands(self, obj):
        brands = list(obj.brands.only("id", "name")[:20])
        if not brands:
            return "—"
        badges = format_html_join(
            "",
            '<span style="display:inline-block; background:#e9ecef; padding:2px 8px; margin:2px; border-radius:12px; font-size:12px;">'
            '<a href="/admin/brands/brand/{}/change/" style="text-decoration:none; color:#0066cc;">{}</a></span>',
            ((str(brand.id), brand.name) for brand in brands),
        )
        if obj.brands_count > len(brands):
            badges += format_html("<span>+ еще {}</span>", obj.brands_count - len(brands))
        return format_html("<div>{}</div>", badges)

    @admin.display(description="Собственные номенклатуры")
    def show_owned(self, obj):
        return self._nomenclature_links(obj.owned_nomenclatures, obj.owned_count)

    @admin.display(description="Арендует")
    def show_rented(self, obj):
        return self._nomenclature_links(obj.rented_nomenclatures, obj.rented_count)

    @staticmethod
    def _nomenclature_links(queryset, total):
        nomenclatures = list(queryset.only("id", "name")[:20])
        if not nomenclatures:
            return "—"
        links = format_html_join(
            "",
            "<li><a href='/admin/nomenclatures/nomenclature/{}/change/' target='_blank'>{}</a></li>",
            ((str(nomenclature.id), nomenclature.name) for nomenclature in nomenclatures),
        )
        if total > len(nomenclatures):
            links += format_html("<li><em>... и еще {} записей</em></li>", total - len(nomenclatures))
        return format_html("<ul style='margin:0; padding-left:20px;'>{}</ul>", links)
