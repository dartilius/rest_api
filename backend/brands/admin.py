from django.contrib import admin
from django.utils.html import format_html, format_html_join

from brands.models import Brand

STATUSES = {
    0: True,
    1: False,
}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Администрирование брендов."""
    list_display = ("id", "name", "is_deleted", "code1c")
    search_fields = ("name",)
    show_full_result_count = False
    readonly_fields = ("show_nomenclatures", "code1c")  # показываем блок только для чтения

    @admin.display(description="Удалён")
    def status(self, obj):
        try:
            return STATUSES[obj.is_deleted]
        except AttributeError:
            return None

    def get_queryset(self, request):
        # чтобы показывались все бренды, включая soft-deleted
        return Brand.all_objects.all()

    @admin.display(description="Связанные номенклатуры")
    def show_nomenclatures(self, obj):
        """Вывод списка связанных номенклатур с кликабельными ссылками."""
        qs = obj.nomenclatures.all()
        if not qs.exists():
            return "Нет связанных номенклатур"

        # создаём список ссылок
        links = format_html_join(
            "",
            "<li><a href='/admin/nomenclatures/nomenclature/{}/change/'>{}</a></li>",
            ((n.id, n.name) for n in qs),
        )
        return format_html("<ul>{}</ul>", links)
