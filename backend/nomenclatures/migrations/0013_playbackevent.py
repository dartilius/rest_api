from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("nomenclatures", "0012_nomenclature_broadcast")]
    operations = [
        migrations.CreateModel(
            name="PlaybackEvent",
            fields=[
                ("event_id", models.UUIDField(primary_key=True, editable=False, serialize=False)),
                ("installation_id", models.UUIDField(null=True, blank=True, editable=False)),
                ("playback_id", models.UUIDField(db_index=True, verbose_name="Воспроизведение")),
                ("event_sequence", models.PositiveIntegerField(verbose_name="Номер события")),
                ("event_type", models.CharField(max_length=16, verbose_name="Событие", choices=[
                    ("started", "Начато"), ("paused", "Пауза"), ("resumed", "Продолжено"),
                    ("completed", "Завершено полностью"), ("interrupted", "Прервано"), ("error", "Ошибка"),
                ])),
                ("occurred_at", models.DateTimeField(verbose_name="Время на плеере")),
                ("received_at", models.DateTimeField(auto_now_add=True, verbose_name="Сохранено сервером")),
                ("media_type", models.CharField(max_length=8, verbose_name="Контент", choices=[
                    ("music", "Музыка"), ("video", "Фоновое видео"), ("image", "Фоновая картинка"), ("ad", "Реклама"),
                ])),
                ("file_id", models.UUIDField(verbose_name="Файл")),
                ("order_id", models.UUIDField(null=True, blank=True, verbose_name="Заказ")),
                ("order_revision", models.PositiveIntegerField(null=True, blank=True, verbose_name="Редакция заказа")),
                ("position_ms", models.PositiveBigIntegerField(verbose_name="Позиция, мс")),
                ("duration_ms", models.PositiveBigIntegerField(verbose_name="Длительность, мс")),
                ("reason", models.CharField(max_length=512, null=True, blank=True, verbose_name="Причина")),
                ("payload", models.JSONField(editable=False)),
                ("nomenclature", models.ForeignKey(to="nomenclatures.nomenclature", related_name="playback_events",
                    on_delete=django.db.models.deletion.CASCADE, verbose_name="Точка вещания")),
            ],
            options={
                "db_table": "player_playback_event",
                "verbose_name": "Событие эфира плеера", "verbose_name_plural": "События эфира плеера",
                "ordering": ("-received_at", "-event_sequence"),
                "indexes": [
                    models.Index(fields=("nomenclature", "occurred_at"), name="player_event_station_time_idx"),
                    models.Index(fields=("order_id", "occurred_at"), name="player_event_order_time_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("nomenclature", "playback_id", "event_sequence"), name="player_playback_sequence_uniq"),
                    models.UniqueConstraint(fields=("nomenclature", "playback_id"), condition=models.Q(event_type__in=("completed", "interrupted", "error")), name="player_playback_terminal_uniq"),
                ],
            },
        ),
    ]
