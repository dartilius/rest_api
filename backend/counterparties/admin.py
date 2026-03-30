from django.contrib import admin
from django.utils.html import format_html, format_html_join

from counterparties.models import Counterparty, CounterpartyContactInfo


# ========= Inline для контактной информации =========
class ContactInfoInline(admin.TabularInline):
    model = CounterpartyContactInfo
    extra = 1
    readonly_fields = ("id",)
    fields = (
        "type",
        "meaning",
        "vidtel",
        "vidmail",
        "basic",
        "comment",
    )


# ========= Admin для контрагентов =========
@admin.register(Counterparty)
class CounterpartiesAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_active",
        "code1c",
        "owned_count",
        "rented_count",
        "brands_count",  # 👈 ИСПРАВЛЕНО: brands_count вместо counter_parties_count
        "counter_parties_count",
    )

    search_fields = ("first_name", "middle_name", "last_name", "keyword")
    readonly_fields = ("show_owned", "show_rented", "code1c", "display_brands", "brands_count")
    inlines = [ContactInfoInline]

    fieldsets = (
        ("Основная информация", {
            "fields": (
                "first_name",
                "middle_name",
                "last_name",
                "keyword",
                "opf",
                "code1c",
                "is_active",
            ),
        }),
        ("Бренды", {
            "fields": ("display_brands", "brands_count"),  # 👈 Добавлен счетчик брендов
        }),
        ("Описание", {
            "fields": ("description",),
        }),
        ("Свои номенклатуры (legalEntity)", {
            "fields": ("show_owned",),
        }),
        ("Арендованные номенклатуры (tenants)", {
            "fields": ("show_rented",),
        }),
        ("Контактные лица", {
            "fields": ("contact_persons",),
        }),
    )

    # ========= Queryset =========
    def get_queryset(self, request):
        return Counterparty.active.prefetch_related(
            "brands",  # 👈 Добавлен prefetch для брендов
            "contact_persons",
            "contacts"
        ).select_related("address").all()

    # ========= Бренды =========
    @admin.display(description="Бренды КА")
    def display_brands(self, obj):
        """Отображение брендов в виде карточек"""
        if not obj or not obj.pk:
            return "—"

        qs = obj.brands.all()
        if not qs.exists():
            return "—"

        # Вариант с тегами (более современный вид)
        badges = format_html_join(
            "",
            '<span style="display:inline-block; background:#e9ecef; padding:2px 8px; margin:2px; border-radius:12px; font-size:12px;">'
            '<a href="/admin/brands/brand/{}/change/" style="text-decoration:none; color:#0066cc;">{}</a>'
            '</span>',
            ((str(b.id), b.name) for b in qs)
        )
        return format_html("<div>{}</div>", badges)

    @admin.display(description="Количество брендов")
    def brands_count(self, obj):
        """Счетчик брендов"""
        if not obj or not obj.pk:
            return 0
        return obj.brands.count()  # 👈 ИСПРАВЛЕНО: brands.count()

    # ========= Счётчики =========
    @admin.display(description="Своих номенклатур")
    def owned_count(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.owned_nomenclatures.count()

    @admin.display(description="Арендованных номенклатур")
    def rented_count(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.rented_nomenclatures.count()

    @admin.display(description="Контактных лиц")
    def counter_parties_count(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.contact_persons.count()

    # ========= Блоки отображения =========
    @admin.display(description="Собственные номенклатуры")
    def show_owned(self, obj):
        if not obj or not obj.pk:
            return "—"

        qs = obj.owned_nomenclatures.all()
        if not qs.exists():
            return "—"

        links = format_html_join(
            "",
            "<li><a href='/admin/nomenclatures/nomenclature/{}/change/' target='_blank'>{}</a></li>",
            ((str(n.id), n.name) for n in qs[:20]),  # 👈 Ограничиваем количество для производительности
        )

        total = qs.count()
        if total > 20:
            links += format_html("<li><em>... и еще {} записей</em></li>", total - 20)

        return format_html("<ul style='margin:0; padding-left:20px;'>{}</ul>", links)

    @admin.display(description="Арендует")
    def show_rented(self, obj):
        if not obj or not obj.pk:
            return "—"

        qs = obj.rented_nomenclatures.all()
        if not qs.exists():
            return "—"

        links = format_html_join(
            "",
            "<li><a href='/admin/nomenclatures/nomenclature/{}/change/' target='_blank'>{}</a></li>",
            ((str(n.id), n.name) for n in qs[:20]),  # 👈 Ограничиваем количество для производительности
        )

        total = qs.count()
        if total > 20:
            links += format_html("<li><em>... и еще {} записей</em></li>", total - 20)

        return format_html("<ul style='margin:0; padding-left:20px;'>{}</ul>", links)