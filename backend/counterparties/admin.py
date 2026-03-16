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
        "counter_parties_count",
        "display_brands"
    )

    search_fields = ("first_name", "middle_name", "last_name", "keyword")
    readonly_fields = ("show_owned", "show_rented", "code1c")
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
            "fields": ("brands",),
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
        return Counterparty.active.prefetch_related("brands", "contact_persons", "contacts").select_related("address").all()

    # ========= Бренды =========
    @admin.display(description="Бренды КА")
    def display_brands(self, obj):
        if not obj or not obj.pk:
            return "—"
        qs = obj.brands.all()
        if not qs.exists():
            return "—"
        # формируем список ссылок на бренды
        links = format_html_join(
            "",
            "<li><a href='/admin/brands/brand/{}/change/'>{}</a></li>",
            ((b.id, b.name) for b in qs)
        )
        return format_html("<ul>{}</ul>", links)

    # ========= Счётчики (ВАЖНО: obj может быть None) =========
    @admin.display(description="Своих")
    def owned_count(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.owned_nomenclatures.count()

    @admin.display(description="Арендованных")
    def rented_count(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.rented_nomenclatures.count()

    @admin.display(description="КЛ")
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
            "<li><a href='/admin/nomenclatures/nomenclature/{}/change/'>{}</a></li>",
            ((n.id, n.name) for n in qs),
        )
        return format_html("<ul>{}</ul>", links)

    @admin.display(description="Арендует")
    def show_rented(self, obj):
        if not obj or not obj.pk:
            return "—"

        qs = obj.rented_nomenclatures.all()
        if not qs.exists():
            return "—"

        links = format_html_join(
            "",
            "<li><a href='/admin/nomenclatures/nomenclature/{}/change/'>{}</a></li>",
            ((n.id, n.name) for n in qs),
        )
        return format_html("<ul>{}</ul>", links)
