from pathlib import PurePosixPath
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from api import APIBaseObjectModel, Article, UUIDPKField
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


class TypesOfPlaceBroadcast(APIBaseObjectModel):
    type_of_place = models.ForeignKey(
            "nomenclatures.TypeOfPlace",
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name="type_of_place",
            verbose_name="Тип места размещения",
    )
    title = models.CharField("Название формата", max_length=250)
    format_type = models.CharField("Тип формата", max_length=32, choices=DEMO_FORMAT_CHOICES)
    description = models.TextField("Описание", blank=True, max_length=5000)
    class Meta:
        db_table = "types_of_place_broadcast"
        verbose_name = "Формат размещения"
        verbose_name_plural = "Форматы размещения"
        constraints = [models.UniqueConstraint(fields=("type_of_place", "format_type"), name="types_of_place_broadcast_unique")]

class TypeOfFormats(APIBaseObjectModel):
    format_type = models.CharField("Тип формата", max_length=32, choices=DEMO_FORMAT_CHOICES)
    description = models.TextField("Описание", blank=True, max_length=5000)
    demo = models.ForeignKey(
        BroadcastDemo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="type_of_formats_demo",
        verbose_name="Демо вещания",
    )
    class Meta:
        db_table = "type_of_formats"
        verbose_name = "Тип формата"
        verbose_name_plural = "Типы форматов"
        constraints = [models.UniqueConstraint(fields=("format_type",), name="type_of_formats_unique")]

class BroadcastLanding(models.Model):
    title = models.CharField("Заголовок", max_length=250)
    description = models.TextField("Описание", blank=True, max_length=5000)
    logo_brands = models.ManyToManyField(
        "brands.Brand",
        verbose_name="Бренды для блока логотипов",
        blank=True,
        related_name="broadcast_landings",
    )
    format_type = models.ForeignKey(
        TypesOfPlaceBroadcast,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="broadcast_landing_format_type",
        verbose_name="Тип формата",
    )
    demo = models.ForeignKey(
        BroadcastDemo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="broadcast_landing_demo",
        verbose_name="Демо вещания",
    )
    class Meta:
        db_table = "broadcast_landing"
        verbose_name = "Лендинг корп вещания"
        verbose_name_plural = "Лендинги корп вещания"

    def __str__(self):
        return self.title
