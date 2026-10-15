"""Django Admin for the unified Order model."""

from datetime import date
import logging

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import format_html

from files.models import Playlist
from orders.models import Order, OrderStationState
from orders.admin_forms import UnifiedOrderAdminForm, order_audio_image_options
from orders.services.unified_order_delivery import enqueue_cancellation, enqueue_order


logger = logging.getLogger(__name__)
_WEEKDAY_LABELS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")


class OrderReportDayForm(forms.Form):
    day = forms.DateField(
        label="День отчёта", input_formats=("%Y-%m-%d",),
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )

    def clean_day(self):
        value = self.cleaned_data["day"]
        if value in (date.min, date.max):
            raise forms.ValidationError("Для этой даты невозможно определить соседние сутки отчёта.")
        return value


def _enqueue_order_after_commit(order_id):
    order = Order.objects.select_related("owner", "nomenclature", "playlist").get(pk=order_id)
    try:
        enqueue_order(order)
    except Exception:
        # The order remains visible for correction even when delivery fails.
        order.status = 4
        order.save(update_fields=["status"])
        logger.exception("Не удалось сформировать команду Player для заказа %s", order.pk)


def _enqueue_cancellation_after_commit(order_id):
    order = Order.objects.select_related("owner", "nomenclature", "playlist").get(pk=order_id)
    try:
        enqueue_cancellation(order)
    except Exception:
        logger.exception("Не удалось сформировать отмену заказа Player %s", order.pk)


def _enqueue_cancellations_after_commit(order_ids):
    for order_id in order_ids:
        _enqueue_cancellation_after_commit(order_id)


def _enqueue_orders_after_commit(order_ids):
    for order_id in order_ids:
        _enqueue_order_after_commit(order_id)


class OrderDeliveryFilter(admin.SimpleListFilter):
    title = "Доставка заказа"
    parameter_name = "delivery"

    def lookups(self, request, model_admin):
        return (("queued", "В очереди отправки"), ("delivered", "Отправлен, ждёт подтверждения"),
                ("applied", "Применён к расписанию"), ("cancelling", "Ожидает отмены"),
                ("cancelled", "Отменён"), ("failed", "Ошибка"))

    def queryset(self, request, queryset):
        if self.value() == "cancelled":
            return queryset.filter(Q(status=3) | Q(station_state__status="cancelled"))
        if self.value() == "cancelling":
            return queryset.filter(station_state__desired_action="cancel").exclude(station_state__status="cancelled")
        if self.value() == "failed":
            return queryset.filter(Q(status=4) | Q(station_state__status="failed"))
        if self.value() in ("queued", "delivered", "applied"):
            return queryset.filter(station_state__status=self.value(), station_state__desired_action="apply")
        return queryset


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Single place to create advertising and background broadcast orders."""

    list_display = (
        "name", "placement", "nomenclature", "playlist", "schedule_summary",
        "period_summary", "status", "delivery_state", "first_air_confirmation", "plan_fact_link",
    )
    list_filter = ("placement", "playback_policy", "is_permanent", OrderDeliveryFilter)
    search_fields = ("id", "name", "nomenclature__name", "playlist__name")
    raw_id_fields = ("nomenclature",)
    autocomplete_fields = ("playlist",)
    readonly_fields = ("owner", "revision", "created", "status", "delivery_state", "playback_evidence", "first_air_confirmation", "plan_fact_link")
    form = UnifiedOrderAdminForm
    change_form_template = "admin/orders/order/change_form.html"

    class Media:
        js = ("orders/order_form.js",)
        css = {"all": ("orders/order_form.css",)}
    show_full_result_count = False
    fieldsets = (
        ("1. Что и где воспроизводить", {"fields": ("name", "placement", "nomenclature", "playlist", "description")}),
        ("2. Когда воспроизводить", {"fields": (
            "starts_at", "is_permanent", "ends_at", "all_days", "weekdays", "weekdays_control_present",
        )}),
        ("3. Расписание рекламы", {"fields": ("playback_policy", "times_in_hour", "offset_minutes", "offset_seconds", "start_time", "end_time"), "classes": ("order-ad-schedule",)}),
        ("4. Звук и фоновый контент", {"fields": ("advertising_audio", "suppress_background_audio", "suppress_background_visual"), "classes": ("order-ad-options",)}),
        ("5. Очерёдность и картинки", {"fields": ("order_weight", "image_duration_seconds", "audio_images")}),
        ("Доставка и первый выход", {"fields": ("delivery_state", "first_air_confirmation", "plan_fact_link")}),
        ("История заказа", {"fields": ("status", "playback_evidence", "owner", "revision", "created"), "classes": ("collapse",)}),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is not None:
            return self.fieldsets
        return (
            ("1. Что и где воспроизводить", {"fields": ("name", "placement", "target_nomenclatures", "playlist", "description")}),
            *self.fieldsets[1:5],
        )

    def get_urls(self):
        return [
            path(
                "audio-image-options/",
                self.admin_site.admin_view(self.audio_image_options),
                name="orders_order_audio_image_options",
            ),
            path("<path:object_id>/plan-fact/", self.admin_site.admin_view(self.plan_fact_report),
                 name="orders_order_plan_fact"),
        ] + super().get_urls()

    def audio_image_options(self, request):
        if not (
            self.has_change_permission(request)
            or self.has_add_permission(request)
        ):
            raise PermissionDenied
        playlist_id = request.GET.get("playlist")
        try:
            playlist = Playlist.objects.get(pk=playlist_id)
        except (Playlist.DoesNotExist, ValidationError, ValueError, TypeError):
            return JsonResponse(
                {"error": "Выберите существующий плейлист."},
                status=400,
            )
        return JsonResponse(order_audio_image_options(playlist))

    def _order_parameter(self, obj, key, default="Не задано"):
        parameters = obj.parameters if isinstance(obj.parameters, dict) else {}
        return parameters.get(key, default)

    @admin.display(description="Расписание")
    def schedule_summary(self, obj):
        weekdays = self._weekdays_summary(obj)
        if obj.placement == "background":
            return f"По рабочему времени точки; {weekdays}"
        label = obj.get_playback_policy_display()
        if obj.playback_policy not in ("continuous", "event"):
            return f"{label}; {self._order_parameter(obj, 'times_in_hour', '—')} выходов/час; {weekdays}"
        return label

    def _weekdays_summary(self, obj):
        weekdays = self._order_parameter(obj, "weekdays", None)
        if weekdays is None or weekdays == list(range(7)):
            return "каждый день"
        if not isinstance(weekdays, list) or any(type(day) is not int or not 0 <= day <= 6 for day in weekdays):
            return "дни указаны некорректно"
        return ", ".join(_WEEKDAY_LABELS[day] for day in weekdays)

    @admin.display(description="Период")
    def period_summary(self, obj):
        start = date_format(obj.starts_at, "SHORT_DATETIME_FORMAT") if obj.starts_at else "После загрузки"
        end = date_format(obj.ends_at, "SHORT_DATETIME_FORMAT") if obj.ends_at else "Без даты окончания"
        return f"{start} → {end}"

    @admin.display(description="Выходов в час")
    def times_in_hour(self, obj):
        return self._order_parameter(obj, "times_in_hour")

    @admin.display(description="Начинать показы с")
    def start_time(self, obj):
        return self._order_parameter(obj, "start_time")

    @admin.display(description="Заканчивать показы в")
    def end_time(self, obj):
        return self._order_parameter(obj, "end_time")

    def _offset_seconds(self, obj):
        value = self._order_parameter(obj, "timedelta")
        if type(value) in (int, float):
            return int(value * 60)
        try:
            hours, minutes, seconds = map(int, value.split(":"))
            return hours * 3600 + minutes * 60 + seconds
        except (AttributeError, ValueError):
            return 0

    @admin.display(description="Отступ, минут")
    def offset_minutes(self, obj):
        return self._offset_seconds(obj) // 60

    @admin.display(description="Дополнительно секунд")
    def offset_seconds(self, obj):
        return self._offset_seconds(obj) % 60

    @admin.display(description="Приоритет заказа")
    def order_weight(self, obj):
        return self._order_parameter(obj, "weight", 50)

    @admin.display(description="Показ картинки")
    def image_duration_seconds(self, obj):
        value = self._order_parameter(obj, "image_duration_seconds", None)
        return f"{value} сек." if value is not None else "По настройкам плеера"

    @admin.display(description="Звук рекламы")
    def advertising_audio(self, obj):
        return "Без звука" if self._order_parameter(obj, "audio_muted", False) else "Со звуком"

    @admin.display(description="План/факт")
    def plan_fact_link(self, obj):
        if obj is None or not obj.pk or obj._state.adding:
            return "Доступен после создания заказа"
        if obj.placement != "advertising":
            return "—"
        return format_html('<a href="{}">План/факт за день</a>',
                           reverse("admin:orders_order_plan_fact", args=[obj.pk]))

    def plan_fact_report(self, request, object_id):
        if not self.has_view_permission(request):
            raise PermissionDenied
        obj = self.get_object(request, object_id)
        if obj is None or obj.placement != "advertising":
            raise Http404
        if not self.has_view_permission(request, obj):
            raise PermissionDenied
        form = OrderReportDayForm(request.GET if "day" in request.GET else {"day": timezone.now().date().isoformat()})
        report = None
        if form.is_valid():
            from orders.services.order_plan_fact import report_for_order
            report = report_for_order(obj, form.cleaned_data["day"])
        return TemplateResponse(request, "admin/orders/order/plan_fact.html", {
            **self.admin_site.each_context(request), "title": "План/факт рекламы за день",
            "opts": self.model._meta, "original": obj, "form": form, "report": report,
            "order_url": reverse("admin:orders_order_change", args=[obj.pk]),
            "report_now": timezone.now(), "server_timezone": settings.TIME_ZONE,
        }, status=200 if not form.errors else 400)

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user
        if change:
            previous = Order.objects.select_for_update().get(pk=obj.pk)
            obj.revision = previous.revision + 1
        super().save_model(request, obj, form, change)
        if change:
            order_ids = [obj.pk]
        else:
            target_nomenclatures = list(form.cleaned_data["target_nomenclatures"])
            copies = [
                Order(
                    name=obj.name,
                    description=obj.description,
                    placement=obj.placement,
                    playback_policy=obj.playback_policy,
                    nomenclature=nomenclature,
                    playlist=obj.playlist,
                    starts_at=obj.starts_at,
                    ends_at=obj.ends_at,
                    is_permanent=obj.is_permanent,
                    suppress_background_audio=obj.suppress_background_audio,
                    suppress_background_visual=obj.suppress_background_visual,
                    status=obj.status,
                    parameters=obj.parameters,
                    owner=obj.owner,
                )
                for nomenclature in target_nomenclatures[1:]
            ]
            created_orders = Order.objects.bulk_create(copies)
            order_ids = [obj.pk, *(order.pk for order in created_orders)]
        if obj.status in (0, 1):
            for order in Order.objects.filter(pk__in=order_ids).select_related("nomenclature", "playlist", "owner"):
                enqueue_order(order)
        if not change and len(order_ids) > 1:
            self.message_user(
                request,
                f"Создано заказов для точек: {len(order_ids)}.",
                messages.SUCCESS,
            )

    @admin.action(description="Повторно отправить выбранные заказы Player")
    def resend_orders(self, request, queryset):
        order_ids = list(queryset.filter(status__in=(0, 1)).values_list("pk", flat=True))
        if not order_ids:
            self.message_user(request, "Нет ожидающих или активных заказов для отправки.", messages.WARNING)
            return
        with transaction.atomic():
            for order in Order.objects.select_for_update().filter(pk__in=order_ids, is_active=True):
                enqueue_order(order)
        self.message_user(request, f"Заказов поставлено в очередь: {len(order_ids)}.", messages.SUCCESS)

    @admin.action(description="Отменить выбранные заказы эфира")
    def cancel_orders(self, request, queryset):
        eligible = list(queryset.filter(is_active=True).exclude(status__in=(2, 3)))
        order_ids = [order.pk for order in eligible]
        if not order_ids:
            self.message_user(request, "Нет заказов, доступных для отмены.", messages.WARNING)
            return
        updated = 0
        with transaction.atomic():
            for order in Order.objects.select_for_update().filter(pk__in=order_ids, is_active=True):
                order.is_active = False
                order.revision += 1
                order.save(update_fields=("is_active", "revision"))
                enqueue_cancellation(order)
                updated += 1
        self.message_user(request, f"Запрошена отмена заказов: {updated}. Ожидается подтверждение Player.", messages.SUCCESS)

    def get_queryset(self, request):
        queryset = self.model.objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            queryset = queryset.order_by(*ordering)
        from orders.services.order_progress import with_order_progress
        return with_order_progress(queryset.select_related("nomenclature", "playlist", "owner", "station_state"))

    @admin.display(description="Первый выход подтверждён")
    def first_air_confirmation(self, obj):
        if obj is None or not obj.pk:
            return "Заказ ещё не создан"
        try:
            revision = obj.station_state.on_air_revision
        except OrderStationState.DoesNotExist:
            revision = None
        return f"Да, версия {revision}" if revision is not None else "Ожидается первый запуск Player"

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return (*fields, "nomenclature", "placement") if obj else fields

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (obj is None or obj.is_active)

    @admin.display(description="Подтверждение станции")
    def delivery_state(self, obj):
        if obj is None or not obj.pk:
            return "Заказ ещё не отправлен"
        try:
            state = obj.station_state
        except OrderStationState.DoesNotExist:
            return "Старый протокол: подробное подтверждение отсутствует"
        prefix = "Отмена: " if state.desired_action == "cancel" else ""
        labels = {"queued": "В очереди", "delivered": "Доставлен, ждёт подтверждения", "applied": "Применён к расписанию", "cancelled": "Отменён", "failed": "Ошибка", "superseded": "Заменён новой командой"}
        from orders.services.order_progress import delivery_progress
        progress = delivery_progress(obj)
        if progress:
            observation = f"{progress['label']}; проверено файлов {progress['files_verified']} из {progress['files_total']}"
            if not progress["fresh"]:
                observation = f"Последние данные устарели: {observation}"
            return f"{observation} (редакция {state.desired_revision})"
        return f"{prefix}{labels.get(state.status, state.status)} (редакция {state.desired_revision})" + (f": {state.last_error}" if state.last_error else "")

    actions = ("resend_orders", "cancel_orders")

    @admin.display(description="Подтверждённый запуск")
    def playback_evidence(self, obj):
        if obj is None or not obj.pk:
            return "Событий ещё нет"
        from nomenclatures.player_v2.playback.models import PlaybackEvent
        try:
            revision = obj.station_state.on_air_revision
        except OrderStationState.DoesNotExist:
            revision = None
        if revision is None:
            return "Первый запуск ещё не подтверждён"
        event = PlaybackEvent.objects.filter(
            order_id=obj.pk, nomenclature_id=obj.nomenclature_id,
            order_revision=revision, event_type="started", event_sequence=1,
        ).order_by("occurred_at", "pk").first()
        if event is None:
            return "Плеер ещё не передал подтверждённых событий"
        return (
            f"{event.get_event_type_display()}, редакция {event.order_revision}; "
            f"время плеера {event.occurred_at:%d.%m.%Y %H:%M:%S}. "
            "Последующие выходы доступны в статистике и плане/факте."
        )
