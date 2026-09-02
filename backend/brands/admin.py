"""Административный интерфейс для модели Brand."""

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html, format_html_join

from brands.models import Brand


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Администрирование брендов, включая мягко удалённые записи."""

    list_display = ("id", "name", "is_deleted", "code1c", "nomenclature_count", "slug")
    search_fields = ("name",)
    show_full_result_count = False
    readonly_fields = ("show_nomenclatures", "code1c")
    list_per_page = 50

    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "code1c", "description", "logotype", "is_deleted"),
        }),
        ("Связанные данные", {
            "fields": ("show_nomenclatures",),
            "description": "Список номенклатур, связанных с данным брендом.",
        }),
    )

    def get_queryset(self, request):
        """Добавляет счётчик номенклатур без загрузки самих номенклатур."""
        return (
            Brand.all_objects
            .annotate(nomenclature_count=Count("nomenclatures"))
            .only(
                "id", "name", "code1c", "slug", "description", "is_deleted", "created",
            )
        )

    @admin.display(description="Кол-во номенклатур", ordering="nomenclature_count")
    def nomenclature_count(self, obj):
        return obj.nomenclature_count

    @admin.display(description="Связанные номенклатуры")
    def show_nomenclatures(self, obj):
        """Показывает первые 20 связанных номенклатур на странице бренда."""
        nomenclatures = list(obj.nomenclatures.only("id", "name")[:20])
        if not nomenclatures:
            return "Нет связанных номенклатур"

        links = format_html_join(
            "",
            "<li><a href='/admin/nomenclatures/nomenclature/{}/change/'>{}</a></li>",
            ((str(nomenclature.id), nomenclature.name) for nomenclature in nomenclatures),
        )
        total = obj.nomenclature_count
        if total > len(nomenclatures):
            links += format_html("<li><em>... и еще {} записей</em></li>", total - len(nomenclatures))

        return format_html("<ul style='margin:0; padding-left:20px;'>{}</ul>", links)
