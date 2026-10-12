# Generated manually for the unified broadcast-order rollout.

import uuid

import api.base_objects
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0005_playlistitem_playlistitemvisual"),
        ("orders", "0003_bgorder_is_permanent_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", api.base_objects.UUIDPKField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name="Уникальный идентификатор")),
                ("name", models.CharField(max_length=255, verbose_name="Название")),
                ("is_active", models.BooleanField(default=True, verbose_name="Актуальность")),
                ("created", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("description", models.TextField(blank=True, null=True, verbose_name="Описание")),
                ("placement", models.CharField(choices=[("background", "Фоновый контент"), ("advertising", "Реклама")], max_length=16, verbose_name="Размещение в эфире")),
                ("playback_policy", models.CharField(choices=[("continuous", "Непрерывно"), ("workday", "В рабочее время точки"), ("hourly_slots", "Выходы в течение часа"), ("fixed_time", "В заданные часы"), ("open_offset", "От открытия со смещением"), ("close_offset", "До закрытия со смещением"), ("open_to_fixed", "От открытия до заданного времени"), ("fixed_to_close", "От заданного времени до закрытия"), ("event", "По событию")], default="workday", max_length=16, verbose_name="Правило воспроизведения")),
                ("starts_at", models.DateTimeField(blank=True, null=True, verbose_name="Начало вещания")),
                ("ends_at", models.DateTimeField(blank=True, null=True, verbose_name="Окончание вещания")),
                ("is_permanent", models.BooleanField(default=False, verbose_name="Бессрочный заказ")),
                ("suppress_background_audio", models.BooleanField(default=False, verbose_name="Отключать фоновое аудио")),
                ("suppress_background_visual", models.BooleanField(default=False, verbose_name="Отключать фоновый визуальный контент")),
                ("status", models.PositiveSmallIntegerField(choices=[(0, "Ожидает эфира"), (1, "В эфире"), (2, "Завершён"), (3, "Отменён"), (4, "Ошибка")], default=0, verbose_name="Статус")),
                ("parameters", models.JSONField(blank=True, default=dict, verbose_name="Параметры воспроизведения")),
                ("revision", models.PositiveIntegerField(default=1, editable=False, verbose_name="Редакция")),
                ("nomenclature", models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name="broadcast_orders", to="nomenclatures.nomenclature", verbose_name="Рабочая станция")),
                ("owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name="orders", to="users.customuser", verbose_name="Создатель")),
                ("playlist", models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name="broadcast_orders", to="files.playlist", verbose_name="Плейлист")),
            ],
            options={
                "verbose_name": "Заказ эфира",
                "verbose_name_plural": "Заказы эфира",
                "db_table": "broadcast_order",
                "ordering": ("-created",),
            },
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["nomenclature", "status", "starts_at"], name="broadcast_order_ns_start_idx"),
        ),
    ]
