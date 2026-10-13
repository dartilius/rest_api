"""Read-only evidence and daily completed counts in the standard admin theme."""

from datetime import date, datetime, time, timedelta

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, OuterRef, Subquery
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from files.models import File
from nomenclatures.player_v2.playback.models import PlaybackEvent
from nomenclatures.player_v2.playback.service import completed_playbacks
from orders.models import Order


@admin.register(PlaybackEvent)
class PlaybackEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "received_at", "nomenclature", "media_type", "file_name", "order_name", "event_type", "reason")
    list_filter = ("event_type", "media_type", "occurred_at")
    search_fields = ("=event_id", "=playback_id", "=file_id", "=order_id", "nomenclature__name")
    readonly_fields = tuple(field.name for field in PlaybackEvent._meta.fields)
    show_full_result_count = False
    list_per_page = 50
    change_list_template = "admin/nomenclatures/playbackevent/change_list.html"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("nomenclature").annotate(
            file_label=Subquery(File.objects.filter(pk=OuterRef("file_id")).values("name")[:1]),
            order_label=Subquery(Order.objects.filter(pk=OuterRef("order_id")).values("name")[:1]),
        )

    @admin.display(description="Файл")
    def file_name(self, obj):
        return obj.file_label or str(obj.file_id)

    @admin.display(description="Заказ")
    def order_name(self, obj):
        if obj.order_id is None:
            return "Без связи с единым заказом"
        return format_html('<a href="{}">{}</a>', reverse("admin:orders_order_change", args=[obj.order_id]), obj.order_label or str(obj.order_id))

    def get_urls(self):
        return [path("daily/", self.admin_site.admin_view(self.daily_report), name="nomenclatures_playbackevent_daily")] + super().get_urls()

    def daily_report(self, request):
        if not self.has_view_permission(request):
            raise PermissionDenied
        try:
            day = date.fromisoformat(request.GET.get("day", date.today().isoformat()))
        except ValueError:
            day = date.today()
        begin = datetime.combine(day, time.min)
        end = begin + timedelta(days=1)
        rows = list(completed_playbacks().filter(occurred_at__gte=begin, occurred_at__lt=end).values(
            "nomenclature_id", "nomenclature__name", "media_type", "order_id", "file_id",
        ).annotate(completed_count=Count("event_id")).order_by("nomenclature__name", "media_type", "order_id", "file_id")[:1000])
        media_labels = dict(PlaybackEvent.Media.choices)
        file_names = dict(File.objects.filter(pk__in=[row["file_id"] for row in rows]).values_list("pk", "name"))
        order_names = dict(Order.objects.filter(pk__in=[row["order_id"] for row in rows if row["order_id"]]).values_list("pk", "name"))
        for row in rows:
            row["media_label"] = media_labels[row["media_type"]]
            row["file_name"] = file_names.get(row["file_id"], str(row["file_id"]))
            row["order_name"] = order_names.get(row["order_id"], "Без связи с единым заказом")
        return TemplateResponse(request, "admin/nomenclatures/playbackevent/daily.html", {
            **self.admin_site.each_context(request), "title": "Фактические завершённые воспроизведения за день",
            "day": day.isoformat(), "rows": rows, "opts": self.model._meta,
        })
