from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import (
    ForeignKey,
    Model,
    ManyToManyField,
    PositiveIntegerField,
    BooleanField,
    CharField,
    DateTimeField,
)
from django.utils import timezone
from uuid import uuid4

from .dates import current_business_date

from api import UUIDPKField
from api.custom_managers import ActiveManager

DAYS_OF_WEEK = [
    ("mon", "Понедельник"),
    ("tue", "Вторник"),
    ("wed", "Среда"),
    ("thu", "Четверг"),
    ("fri", "Пятница"),
    ("sat", "Суббота"),
    ("sun", "Воскресенье"),
]

COMMERCIAL_STATUS_CHOICES = [
    ("new", "Новый"),
    ("qualified", "Квалифицирован"),
    ("proposal_sent", "Предложение отправлено"),
    ("booked", "Забронирован"),
    ("lost", "Проигран"),
]

LOST_REASON_CHOICES = [
    ("no_contact", "No contact"),
    ("budget", "Budget"),
    ("timing", "Timing"),
    ("inventory", "Inventory"),
    ("competitor", "Competitor"),
    ("other", "Other"),
]

STATUS_TIMESTAMP_FIELDS = {
    "qualified": "qualified_at",
    "proposal_sent": "proposal_sent_at",
    "booked": "booked_at",
    "lost": "lost_at",
}


class PlacementOrder(models.Model):
    id = UUIDPKField()
    code1c = CharField(
        unique=True,
        null=True,
        blank=True,
    )
    name = CharField(max_length=120, blank=True, verbose_name="Название медиаплана")
    plan_number = CharField(max_length=24, unique=True, null=True, blank=True, editable=False)
    revision = PositiveIntegerField(default=1, editable=False)
    manager_comment = models.TextField(blank=True, default="")
    owner = ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="placement_orders",
        verbose_name="КЛ"
    )
    nomenclatures = ManyToManyField(
        "nomenclatures.Nomenclature",
        through="PlacementOrderItem",
        related_name="placement_orders",
        verbose_name="Места размещения"
    )

    start_date = models.DateField(
        verbose_name='Дата начала',
        blank=True,
        null=True
    )
    end_date = models.DateField(
        verbose_name='Дата окончания',
        blank=True,
        null=True
    )
    duration = PositiveIntegerField(
        verbose_name="Кол-во дней"
    )
    all_days = BooleanField(
        default=True,
        verbose_name="Все дни недели"
    )
    days_of_week = ArrayField(
        base_field=CharField(max_length=3, choices=DAYS_OF_WEEK),
        blank=True,
        default=list,
        verbose_name="Дни недели"
    )

    is_active = BooleanField(
        default=True,
        verbose_name='Актуальность'
    )

    created = DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    updated = DateTimeField(auto_now=True)

    commercial_status = CharField(
        max_length=16,
        choices=COMMERCIAL_STATUS_CHOICES,
        default="new",
        db_index=True,
        verbose_name="Commercial status",
    )
    lost_reason = CharField(
        max_length=16,
        choices=LOST_REASON_CHOICES,
        null=True,
        blank=True,
        verbose_name="Lost reason",
    )
    attribution = models.JSONField(null=True, blank=True, verbose_name="Marketing attribution")
    qualified_at = DateTimeField(null=True, blank=True, editable=False)
    proposal_sent_at = DateTimeField(null=True, blank=True, editable=False)
    booked_at = DateTimeField(null=True, blank=True, editable=False)
    lost_at = DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Заказ на размещение"
        verbose_name_plural = "Заказы на размещение"

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        from datetime import timedelta, date as date_type

        errors = {}

        if not self.all_days and not self.days_of_week:
            errors["days_of_week"] = "Укажите дни недели, если all_days = false."
        if self.all_days and self.days_of_week:
            errors["days_of_week"] = "Нельзя указывать дни недели при all_days = true."

        today = current_business_date()
        min_start = today + timedelta(days=2)

        def to_date(value):
            if value is None:
                return None
            if isinstance(value, date_type):
                return value
            if hasattr(value, 'date'):
                return value.date()
            return value

        start = to_date(self.start_date)
        end = to_date(self.end_date)

        if start and start < min_start:
            errors["start_date"] = "Дата начала должна быть минимум через 2 дня от текущей даты."

        if start and end and end <= start:
            errors["end_date"] = "Дата окончания должна быть минимум на 1 день позже даты начала."

        if self.commercial_status == "lost" and not self.lost_reason:
            errors["lost_reason"] = "A lost order requires a lost reason."
        if self.commercial_status != "lost" and self.lost_reason:
            errors["lost_reason"] = "Lost reason is allowed only for lost orders."

        if self.attribution is not None:
            from .marketing import validate_attribution_payload

            try:
                validate_attribution_payload(self.attribution)
            except ValueError as exc:
                errors["attribution"] = str(exc)

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Set a funnel timestamp once, on the first transition into that status."""
        if not self.name:
            self.name = f"Медиаплан {current_business_date():%Y-%m-%d}"
        if not self.plan_number:
            prefix = current_business_date().strftime("MP-%Y%m%d-")
            candidate = f"{prefix}{uuid4().hex[:8].upper()}"
            while type(self).objects.filter(plan_number=candidate).exists():
                candidate = f"{prefix}{uuid4().hex[:8].upper()}"
            self.plan_number = candidate
        update_fields = kwargs.get("update_fields")
        if self.pk and self.commercial_status in STATUS_TIMESTAMP_FIELDS:
            previous_status = type(self).objects.filter(pk=self.pk).values_list(
                "commercial_status", flat=True
            ).first()
            timestamp_field = STATUS_TIMESTAMP_FIELDS[self.commercial_status]
            if previous_status != self.commercial_status and not getattr(self, timestamp_field):
                setattr(self, timestamp_field, timezone.now())
                if update_fields is not None:
                    kwargs["update_fields"] = set(update_fields) | {timestamp_field}

        if self.commercial_status != "lost":
            self.lost_reason = None
            if update_fields is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"lost_reason"}

        super().save(*args, **kwargs)

class PlacementOrderItem(models.Model):
    """Промежуточная модель — одна строка = одно место в заказе."""

    order = models.ForeignKey(
        PlacementOrder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ"
    )
    nomenclature = models.ForeignKey(
        "nomenclatures.Nomenclature",
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="Место"
    )
    responsible = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placement_order_items",
        verbose_name="Ответственный за размещение"
    )

    class Meta:
        unique_together = ("order", "nomenclature")
        verbose_name = "Место"
        verbose_name_plural = "Места"
