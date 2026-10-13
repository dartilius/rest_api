"""Unified orders for the current Content Player."""

from django.core.exceptions import ValidationError
from django.db import models

from api import APIBaseObjectModel


ORDER_STATUSES = {
    0: "Ожидает эфира",
    1: "В эфире",
    2: "Завершён",
    3: "Отменён",
    4: "Ошибка",
}
ORDER_PLACEMENTS = {"background": "Фоновый контент", "advertising": "Реклама"}
PLAYBACK_POLICIES = {
    "continuous": "Непрерывно",
    "workday": "В рабочее время точки",
    "hourly_slots": "Выходы в течение часа",
    "fixed_time": "В заданные часы",
    "open_offset": "От открытия со смещением",
    "close_offset": "До закрытия со смещением",
    "open_to_fixed": "От открытия до заданного времени",
    "fixed_to_close": "От заданного времени до закрытия",
    "start_to_close": "Реклама с указанного времени",
    "event": "По событию",
}


class Order(APIBaseObjectModel):
    """One broadcast order, whether it is background or advertising."""

    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    placement = models.CharField(max_length=16, choices=ORDER_PLACEMENTS, verbose_name="Размещение в эфире")
    playback_policy = models.CharField(
        max_length=16, choices=PLAYBACK_POLICIES, default="workday", verbose_name="Правило воспроизведения"
    )
    nomenclature = models.ForeignKey(
        "nomenclatures.Nomenclature", related_name="broadcast_orders", on_delete=models.DO_NOTHING,
        verbose_name="Рабочая станция"
    )
    playlist = models.ForeignKey(
        "files.Playlist", related_name="broadcast_orders", on_delete=models.DO_NOTHING, verbose_name="Плейлист"
    )
    starts_at = models.DateTimeField(null=True, blank=True, verbose_name="Начало вещания")
    ends_at = models.DateTimeField(null=True, blank=True, verbose_name="Окончание вещания")
    is_permanent = models.BooleanField(default=False, verbose_name="Бессрочный заказ")
    suppress_background_audio = models.BooleanField(default=False, verbose_name="Отключать фоновое аудио")
    suppress_background_visual = models.BooleanField(default=False, verbose_name="Отключать фоновый визуальный контент")
    status = models.PositiveSmallIntegerField(choices=ORDER_STATUSES, default=0, verbose_name="Статус")
    parameters = models.JSONField(default=dict, blank=True, verbose_name="Параметры воспроизведения")
    revision = models.PositiveIntegerField(default=1, editable=False, verbose_name="Редакция")

    class Meta:
        db_table = "broadcast_order"
        ordering = ("-created",)
        verbose_name = "Заказ эфира"
        verbose_name_plural = "Заказы эфира"
        indexes = [
            models.Index(fields=("nomenclature", "status", "starts_at"), name="broadcast_order_ns_start_idx"),
        ]

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError({"ends_at": "Окончание должно быть позднее начала."})
        if self.is_permanent and self.ends_at is not None:
            raise ValidationError({"ends_at": "У бессрочного заказа не может быть окончания."})
        if self.placement == "advertising" and self.is_permanent:
            raise ValidationError({"is_permanent": "Бессрочным может быть только фоновый заказ."})
        if self.playback_policy == "continuous" and self.placement != "advertising":
            raise ValidationError({"playback_policy": "Непрерывный режим сейчас доступен только рекламе."})
        if self.placement == "background" and self.playback_policy != "workday":
            raise ValidationError({"playback_policy": "Для фонового заказа сейчас доступно только workday."})
        if self.playback_policy == "start_to_close" and not (self.parameters or {}).get("start_time"):
            raise ValidationError({
                "parameters": "Для режима «Реклама с указанного времени» укажите первый выход."
            })


class OrderStationState(models.Model):
    """Desired and confirmed delivery state for one order at its station.

    ``Order.status`` remains the business status exposed by the legacy API.
    This journal deliberately keeps the requested action separate from the
    Player acknowledgement: a cancellation is not confirmed merely because
    the server has queued it.
    """

    class Action(models.TextChoices):
        APPLY = "apply", "Apply"
        CANCEL = "cancel", "Cancel"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        DELIVERED = "delivered", "Delivered"
        RECEIVED = "received", "Received"
        DOWNLOADING = "downloading", "Downloading"
        READY = "ready", "Ready"
        APPLIED = "applied", "Applied"
        CANCELLED = "cancelled", "Cancelled"
        FAILED = "failed", "Failed"
        SUPERSEDED = "superseded", "Superseded"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="station_state")
    nomenclature = models.ForeignKey(
        "nomenclatures.Nomenclature", on_delete=models.DO_NOTHING, related_name="order_delivery_states"
    )
    desired_action = models.CharField(max_length=8, choices=Action.choices, default=Action.APPLY)
    desired_revision = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    command_id = models.UUIDField(null=True, blank=True, unique=True)
    received_revision = models.PositiveIntegerField(null=True, blank=True)
    ready_revision = models.PositiveIntegerField(null=True, blank=True)
    applied_revision = models.PositiveIntegerField(null=True, blank=True)
    on_air_revision = models.PositiveIntegerField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "order_station_state"
        indexes = [
            models.Index(fields=("nomenclature", "status"), name="order_station_state_ns_idx"),
        ]
