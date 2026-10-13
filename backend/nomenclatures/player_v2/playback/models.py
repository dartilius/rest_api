"""PostgreSQL journal of confirmed Player playback events, separate from ClickHouse."""

from django.db import models


class PlaybackEvent(models.Model):
    class Type(models.TextChoices):
        STARTED = "started", "Начато"
        PAUSED = "paused", "Пауза"
        RESUMED = "resumed", "Продолжено"
        COMPLETED = "completed", "Завершено полностью"
        INTERRUPTED = "interrupted", "Прервано"
        ERROR = "error", "Ошибка"

    class Media(models.TextChoices):
        MUSIC = "music", "Музыка"
        VIDEO = "video", "Фоновое видео"
        IMAGE = "image", "Фоновая картинка"
        AD = "ad", "Реклама"

    event_id = models.UUIDField(primary_key=True, editable=False)
    nomenclature = models.ForeignKey(
        "nomenclatures.Nomenclature", on_delete=models.CASCADE,
        related_name="playback_events", verbose_name="Точка вещания",
    )
    installation_id = models.UUIDField(null=True, blank=True, editable=False)
    playback_id = models.UUIDField(db_index=True, verbose_name="Воспроизведение")
    event_sequence = models.PositiveIntegerField(verbose_name="Номер события")
    event_type = models.CharField(max_length=16, choices=Type.choices, verbose_name="Событие")
    occurred_at = models.DateTimeField(verbose_name="Время на плеере")
    received_at = models.DateTimeField(auto_now_add=True, verbose_name="Сохранено сервером")
    media_type = models.CharField(max_length=8, choices=Media.choices, verbose_name="Контент")
    file_id = models.UUIDField(verbose_name="Файл")
    order_id = models.UUIDField(null=True, blank=True, verbose_name="Заказ")
    order_revision = models.PositiveIntegerField(null=True, blank=True, verbose_name="Редакция заказа")
    position_ms = models.PositiveBigIntegerField(verbose_name="Позиция, мс")
    duration_ms = models.PositiveBigIntegerField(verbose_name="Длительность, мс")
    reason = models.CharField(max_length=512, null=True, blank=True, verbose_name="Причина")
    payload = models.JSONField(editable=False)

    class Meta:
        db_table = "player_playback_event"
        verbose_name = "Событие эфира плеера"
        verbose_name_plural = "События эфира плеера"
        ordering = ("-received_at", "-event_sequence")
        constraints = [
            models.UniqueConstraint(
                fields=("nomenclature", "playback_id", "event_sequence"),
                name="player_playback_sequence_uniq",
            ),
            models.UniqueConstraint(
                fields=("nomenclature", "playback_id"),
                condition=models.Q(event_type__in=("completed", "interrupted", "error")),
                name="player_playback_terminal_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=("nomenclature", "occurred_at"), name="player_event_station_time_idx"),
            models.Index(fields=("order_id", "occurred_at"), name="player_event_order_time_idx"),
            models.Index(fields=("received_at",), name="player_event_received_idx"),
            models.Index(fields=("occurred_at",), condition=models.Q(event_type="completed"), name="player_event_completed_idx"),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} · {self.file_id}"
