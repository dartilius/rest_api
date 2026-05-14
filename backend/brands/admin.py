from django.contrib import admin
from django.utils.html import format_html, format_html_join
from brands.models import Brand

STATUSES = {0: True, 1: False}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Администрирование брендов."""
    list_display = ("id", "name", "is_deleted", "code1c", "nomenclature_count", "slug")
    search_fields = ("name",)
    show_full_result_count = False

    readonly_fields = ("show_nomenclatures", "code1c")

    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "code1c", "description", "logotype", "is_deleted"),
        }),
        ("Связанные данные", {
            "fields": ("show_nomenclatures",),
            "description": "Список номенклатур, связанных с данным брендом.",
        }),
    )

    @admin.display(description="Удалён")
    def status(self, obj):
        try:
            return STATUSES[obj.is_deleted]
        except AttributeError:
            return None

    def get_queryset(self, request):
        """Показывать все бренды, включая мягко удалённые."""
        return Brand.all_objects.all()

    @admin.display(description="Связанные номенклатуры")
    def show_nomenclatures(self, obj):
        """Список связанных номенклатур с кликабельными ссылками."""
        qs = obj.nomenclatures.all()
        if not qs.exists():
            return "Нет связанных номенклатур"

        links = format_html_join(
            "",
            "<li><a href='/admin/nomenclatures/nomenclature/{}/change/'>{}</a></li>",
            ((n.id, n.name) for n in qs),
        )
        return format_html("<ul>{}</ul>", links)

    @admin.display(description="Кол-во номенклатур")
    def nomenclature_count(self, obj):
        """Показывает количество связанных номенклатур в списке брендов."""
        return obj.nomenclatures.count()
