from pathlib import PurePosixPath
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models

from .constants import DEMO_FORMAT_CHOICES, MEDIA_RULES


class BroadcastDemo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField("Заголовок", max_length=250)
    format = models.CharField("Формат / сценарий", max_length=32, choices=DEMO_FORMAT_CHOICES)
    description = models.TextField("Описание", blank=True, max_length=5000)
    transcript = models.TextField("Расшифровка", blank=True, max_length=20000)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_published = models.BooleanField("Опубликовано", default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "created", "id")
        verbose_name = "Демо вещания"
        verbose_name_plural = "Демо вещания"
        indexes = [models.Index(fields=("is_published", "format", "sort_order"), name="broadcast_demo_public_idx")]

    def __str__(self):
        return self.title


class BroadcastDemoAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    demo = models.ForeignKey(BroadcastDemo, on_delete=models.CASCADE, related_name="assets")
    file = models.ForeignKey("files.File", on_delete=models.PROTECT, related_name="broadcast_demo_assets")
    role = models.CharField("Роль", max_length=10, choices=[(key, key) for key in MEDIA_RULES])
    caption = models.CharField("Подпись", max_length=250, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ("sort_order", "id")
        verbose_name = "Материал демо"
        verbose_name_plural = "Материалы демо"
        constraints = [models.UniqueConstraint(fields=("demo", "file", "role"), name="broadcast_demo_asset_unique")]

    @property
    def is_playable(self):
        types, extensions = MEDIA_RULES.get(self.role, (set(), set()))
        return bool(self.file.is_active and self.file.source and self.file.type in types
                    and PurePosixPath(str(self.file.source)).suffix.lower() in extensions)

    def clean(self):
        super().clean()
        if self.file_id and not self.is_playable:
            raise ValidationError({"file": "Нужен активный файл подходящего типа и браузерного формата для выбранной роли."})

    def __str__(self):
        return self.caption or str(self.file)
