"""Позиции основных файлов плейлиста и модель из ранее применённой схемы."""

from django.core.exceptions import ValidationError
from django.db import models


class PlaylistItem(models.Model):
    """Основной файл и его позиция. items — обратная связь Django, не обёртка API."""

    playlist = models.ForeignKey(
        "files.Playlist", on_delete=models.CASCADE, related_name="items", verbose_name="Плейлист"
    )
    file = models.ForeignKey(
        "files.File", on_delete=models.PROTECT, related_name="playlist_items", verbose_name="Основной файл"
    )
    position = models.PositiveIntegerField(default=0, verbose_name="Позиция")
    # Поле старой схемы. Приоритет эфира теперь задаёт parameters.weight заказа.
    weight = models.PositiveSmallIntegerField(
        default=100, verbose_name="Вес", help_text="От 0 до 100; используется для случайного выбора."
    )

    class Meta:
        db_table = "playlist_item"
        ordering = ("position", "id")
        verbose_name = "Элемент плейлиста"
        verbose_name_plural = "Элементы плейлиста"
        constraints = [
            models.UniqueConstraint(fields=("playlist", "position"), name="unique_playlist_item_position"),
            models.CheckConstraint(condition=models.Q(weight__lte=100), name="playlist_item_weight_lte_100"),
        ]

    def clean(self):
        super().clean()
        if (
            self.playlist_id
            and self.file_id
            and PlaylistItem.objects.filter(
                playlist_id=self.playlist_id, file_id=self.file_id
            ).exclude(pk=self.pk).exists()
        ):
            raise ValidationError({"file": "Этот файл уже добавлен в плейлист."})
        if self.file_id and not self.file.is_active:
            raise ValidationError({"file": "Нельзя добавить неактивный файл."})

    def __str__(self):
        return f"{self.playlist}: {self.position} — {self.file}"


class PlaylistItemVisual(models.Model):
    """Устаревшая модель из миграции 0005; новые привязки здесь не создаются.

    Сопровождение рекламного аудио хранится в Order.parameters.audio_images.
    Определение оставлено для соответствия уже применённой схеме базы.
    """

    playlist_item = models.ForeignKey(
        PlaylistItem, on_delete=models.CASCADE, related_name="visuals", verbose_name="Элемент плейлиста"
    )
    file = models.ForeignKey(
        "files.File", on_delete=models.PROTECT, related_name="playlist_item_visuals", verbose_name="Картинка"
    )
    position = models.PositiveIntegerField(default=0, verbose_name="Позиция")
    duration_seconds = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Показ, сек.", help_text="Пусто — используется настройка Player."
    )

    class Meta:
        db_table = "playlist_item_visual"
        ordering = ("position", "id")
        verbose_name = "Картинка элемента плейлиста"
        verbose_name_plural = "Картинки элементов плейлиста"
        constraints = [
            models.UniqueConstraint(fields=("playlist_item", "position"), name="unique_playlist_visual_position"),
        ]

    def clean(self):
        super().clean()
        if self.file_id and self.file.type != 2:
            raise ValidationError({"file": "Визуальным сопровождением может быть только картинка."})
        if self.file_id and not self.file.is_active:
            raise ValidationError({"file": "Нельзя добавить неактивную картинку."})

    def __str__(self):
        return f"{self.playlist_item}: {self.position} — {self.file}"
