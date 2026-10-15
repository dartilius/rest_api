from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models

from api import UUIDPKField


class Feedback(models.Model):
    id = UUIDPKField()
    status = models.CharField(max_length=12, default='active', choices=[
        ('active', 'В работе'), ('closed', 'Завершено'),
    ])
    contract_status = models.CharField(max_length=12, default='unknown', choices=[
        ('unknown', 'Не проверено'), ('none', 'Без договора'), ('contract', 'Есть договор'),
    ])
    contract_reference = models.CharField(max_length=120, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    delete_after = models.DateTimeField(null=True, blank=True, db_index=True, editable=False)
    processing_blocked = models.BooleanField(default=False)
    lawful_retention_until = models.DateTimeField(null=True, blank=True)
    lawful_retention_basis = models.TextField(blank=True)
    class RequestType(models.TextChoices):
        GENERAL = "general", "Общее обращение"
        CORPORATE_BROADCAST = "corporate_broadcast", "Корпоративное вещание"

    request_type = models.CharField(max_length=32, choices=RequestType.choices, default=RequestType.GENERAL, db_default=RequestType.GENERAL, db_index=True)
    company = models.CharField("Компания", max_length=250, blank=True, default="", db_default="")
    request_data = models.JSONField("Параметры заявки", blank=True, default=dict, db_default={})
    consent = models.BooleanField("Согласие на обработку данных", default=False, db_default=False)
    consent_at = models.DateTimeField("Дата согласия", null=True, blank=True, editable=False)
    consent_version = models.CharField("Версия текста согласия", max_length=50, blank=True, default="", db_default="", editable=False)
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
    pathname = models.CharField(
        verbose_name="Раздел сайта",
        null=True,
        blank=True,
    )
    brand_id = models.CharField(
        verbose_name="ID бренда",
        null=True,
        blank=True,
    )
    nomenclatures_ids = ArrayField(
        base_field=models.CharField(),
        verbose_name="ID номенклатур",
        null=True,
        blank=True,
    )
    placement_order = models.ForeignKey(
        "placement_order.PlacementOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_requests",
        verbose_name="Placement order",
    )
    attribution = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Marketing attribution",
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

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        if self.status == 'closed' and not self.closed_at:
            raise ValidationError({'closed_at': 'Укажите фактическую дату завершения.'})
        if self.closed_at and self.closed_at > timezone.now():
            raise ValidationError({'closed_at': 'Дата не может быть в будущем.'})
        if self.contract_status == 'contract' and not self.contract_reference:
            raise ValidationError({'contract_reference': 'Укажите ссылку на договор.'})
        if self.lawful_retention_until and not self.lawful_retention_basis:
            raise ValidationError({'lawful_retention_basis': 'Укажите законное основание хранения.'})

    def save(self, *args, **kwargs):
        from datetime import timedelta

        self.delete_after = (
            self.closed_at + timedelta(days=30)
            if self.status == 'closed' and self.closed_at and self.contract_status == 'none'
            else None
        )
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'delete_after'}
        super().save(*args, **kwargs)
