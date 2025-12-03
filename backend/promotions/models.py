from django.contrib.postgres.indexes import GinIndex
from django.db import models

from api import APIBaseObjectModel


# Create your models here.
class Promotion(APIBaseObjectModel):
    start_period = models.DateField(verbose_name="Начало периода", null=True, blank=True)
    end_period = models.DateField(verbose_name="Окончание периода", null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    code1c = models.CharField(max_length=255, null=True, blank=True, verbose_name="Код 1с", unique=True)
    counterparty = models.ForeignKey(
        'counterparties.Counterparty',
        related_name="promotions",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Контрагент"
    )

    class Meta:
        db_table = 'promotions'
        verbose_name = "Акции"
        verbose_name_plural = "Акции"
        ordering = ("-created",)
        indexes = [
            GinIndex(
                name="promotion_name_gin_idx",
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            )
        ]

