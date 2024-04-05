from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.functions import Concat
from users.models import User

TYPES = [
    (0, "Реклама"),
    (1, "Музыка"),
    (2, "Кртинка фон"),
    (3, "Видео фон"),
    (4, "Бегущая строка")
]

BROADCAST_TYPES = [
    (0, "По времени работы точки"),
    (1, "Начало работы + смещение по времени"),
    (2, "Конец работы - смещение по времени"),
    (3, "Конкретные часы"),
    (4, "С открытия до фиксированного часа"),
    (5, "С фиксированного часа до закрытия"),
    (6, "Старт по событию")
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
    source = models.FileField(
        verbose_name='Файл',
        upload_to='files/source/',
        blank=True,
        null=True
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
    file_type = models.PositiveSmallIntegerField(
        choices=TYPES,
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


class PlaylistSetting(models.Model):
    """Натройки плейлиста."""

    broadcast_type = models.PositiveSmallIntegerField(
        choices=BROADCAST_TYPES,
        verbose_name="Тип вещания"
    )
    parameters = models.JSONField(
        verbose_name="Параметры заказа"
    )


class Playlist(models.Model):
    """Плейлисты."""

    name = models.CharField(
        max_length=255,
        verbose_name="Название"
    )
    description = models.TextField(
        verbose_name="Описание"
    )
    files = models.ManyToManyField(
        File,
        through="PlaylistFiles",
        related_name="playlist_files",
        verbose_name="Файлы"
    )
    settings = models.ForeignKey(
        PlaylistSetting,
        related_name="playlist_settings",
        verbose_name="Настройки",
        on_delete=models.CASCADE,
    )


class PlaylistFiles(models.Model):
    """Файл плейлиста."""

    playlist = models.ForeignKey(
        Playlist,
        related_name="playlist",
        verbose_name="Плейлист",
        on_delete=models.CASCADE
    )
    file = models.ForeignKey(
        File,
        related_name="file",
        verbose_name="Файл",
        on_delete=models.CASCADE
    )
    images = models.ManyToManyField(
        File,
        related_name="slides",
        verbose_name="Слайд"
    )
