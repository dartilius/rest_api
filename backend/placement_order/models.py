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


class PlacementOrder(models.Model):
    id = UUIDPKField()
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

    active = ActiveManager()

    class Meta:
        verbose_name = "Заказ на размещение"
        verbose_name_plural = "Заказы на размещение"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.all_days and not self.days_of_week:
            raise ValidationError({
                "days_of_week": "Укажите дни недели, если all_days = false."
            })
        if self.all_days and self.days_of_week:
            raise ValidationError({
                "days_of_week": "Нельзя указывать дни недели при all_days = true."
            })


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
