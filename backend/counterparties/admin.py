from django.contrib import admin
from django.utils.html import format_html, format_html_join

from counterparties.models import Counterparty

STATUSES = {0: True, 1: False}


@admin.register(Counterparty)
class CounterpartiesAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",  # OK — property
        "is_active",
        "code1c",
        "owned_count",
        "rented_count",
        "counter_parties_count",
    )

    search_fields = ("first_name", "middle_name", "last_name", "keyword")

    readonly_fields = ("show_owned", "show_rented", "code1c")

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
        ("Свои номенклатуры (legalEntity)", {
            "fields": ("show_owned",),
        }),
        ("Арендованные номенклатуры (tenants)", {
            "fields": ("show_rented",),
        }),
        ("Контактные лица", {
            "fields": ("contact_persons",)
        }),
    )


    def get_queryset(self, request):
        return Counterparty.active.all()

    # ==== Counts in list display ====
    @admin.display(description="Своих")
    def owned_count(self, obj):
        return obj.owned_nomenclatures.count()

    @admin.display(description="Арендованных")
    def rented_count(self, obj):
        return obj.rented_nomenclatures.count()

    # ==== Display blocks ====
    @admin.display(description="Собственные номенклатуры")
    def show_owned(self, obj):
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
        qs = obj.rented_nomenclatures.all()
        if not qs.exists():
            return "—"
        links = format_html_join(
            "",
            "<li><a href='/admin/nomenclatures/nomenclature/{}/change/'>{}</a></li>",
            ((n.id, n.name) for n in qs),
        )
        return format_html("<ul>{}</ul>", links)


    @admin.display(description="Контактное лицо")
    def show_counter_parties(self, obj):
        return ", ".join([n.get_full_name() or n.username for n in obj.contact_persons.all()]) or "Нет КЛ"


    @admin.display(description="КЛ")
    def counter_parties_count(self, obj):
        return obj.contact_persons.count()


