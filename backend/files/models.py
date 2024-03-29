from uuid import uuid4

from django.db import models
from django.db.models.functions import Concat
from backend.users.models import User

TYPES = [
    (0, "Ad"),
    (1, "Music"),
    (2, "BG Image"),
    (3, "BG Video"),
    (4, "Ticker")
]


class Theme(models.Model):
    """Тематики."""

    name = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=True,
        verbose_name="Наименование"
    )


class File(models.Model):
    """Файлы."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Наименование"
    )
    md5hash = models.CharField(
        max_length=32,
        editable=False,
        verbose_name="MD5"
    )
    sha256hash = models.CharField(
        max_length=256,
        editable=False,
        verbose_name="SHA256"
    )
    hash = models.CharField(
        Concat(md5hash, sha256hash),
        max_length=288,
        verbose_name="Комбинированная контрольная сумма"
    )
    length = models.TimeField(
        editable=False,
        verbose_name="Продолжительность"
    )
    size = models.IntegerField(
        editable=False,
        verbose_name="Размер"
    )
    owner = models.ForeignKey(
        User,
        related_name="files",
        blank=True,
        null=True,
        verbose_name="Кто загрузил",
        on_delete=models.SET_NULL
    )
    file_type = models.CharField(
        choices=TYPES,
        max_length=100,
        verbose_name="Тип"
    )
    theme = models.ManyToManyField(
        Theme,
        related_name="files",
        verbose_name="Тематика"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

