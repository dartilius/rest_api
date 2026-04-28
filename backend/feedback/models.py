from django.contrib.postgres.indexes import GinIndex
from django.db import models

from api import UUIDPKField


class Feedback(models.Model):
    id = UUIDPKField()
    code1c = models.CharField(
        verbose_name="Код 1с",
        null=True,
        blank=True,
    )
    name = models.CharField(
        verbose_name="Имя",
        null=True,
        blank=True,
    )
    phone = models.CharField(
        verbose_name="Телефон",
        null=True,
        blank=True,
    )
    email = models.CharField(
        verbose_name="Почта",
        null=True,
        blank=True,
    )
    message = models.CharField(
        verbose_name="Текст обращения",
        null=True,
        blank=True,
    )
    created = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )

    class Meta:
        db_table = "feedback"
        verbose_name = "Обратная связь"
        verbose_name_plural = "Обратные связи"
        ordering = ("-created",)
        indexes = [
            GinIndex(
                name="feedback_name_gin_idx",
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            ),
            models.Index(fields=["name"]),
            models.Index(fields=["code1c"]),
        ]