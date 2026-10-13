# Generated manually for the structured playlist rollout.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0004_alter_file_subtype_alter_tag_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlaylistItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position", models.PositiveIntegerField(default=0, verbose_name="Позиция")),
                (
                    "weight",
                    models.PositiveSmallIntegerField(
                        default=100,
                        help_text="От 0 до 100; используется для случайного выбора.",
                        verbose_name="Вес",
                    ),
                ),
                (
                    "file",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="playlist_items",
                        to="files.file",
                        verbose_name="Основной файл",
                    ),
                ),
                (
                    "playlist",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="files.playlist",
                        verbose_name="Плейлист",
                    ),
                ),
            ],
            options={
                "verbose_name": "Элемент плейлиста",
                "verbose_name_plural": "Элементы плейлиста",
                "db_table": "playlist_item",
                "ordering": ("position", "id"),
            },
        ),
        migrations.CreateModel(
            name="PlaylistItemVisual",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position", models.PositiveIntegerField(default=0, verbose_name="Позиция")),
                (
                    "duration_seconds",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        help_text="Пусто — используется настройка Player.",
                        null=True,
                        verbose_name="Показ, сек.",
                    ),
                ),
                (
                    "file",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="playlist_item_visuals",
                        to="files.file",
                        verbose_name="Картинка",
                    ),
                ),
                (
                    "playlist_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="visuals",
                        to="files.playlistitem",
                        verbose_name="Элемент плейлиста",
                    ),
                ),
            ],
            options={
                "verbose_name": "Картинка элемента плейлиста",
                "verbose_name_plural": "Картинки элементов плейлиста",
                "db_table": "playlist_item_visual",
                "ordering": ("position", "id"),
            },
        ),
        migrations.AddConstraint(
            model_name="playlistitem",
            constraint=models.UniqueConstraint(
                fields=("playlist", "position"), name="unique_playlist_item_position"
            ),
        ),
        migrations.AddConstraint(
            model_name="playlistitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("weight__lte", 100)), name="playlist_item_weight_lte_100"
            ),
        ),
        migrations.AddConstraint(
            model_name="playlistitemvisual",
            constraint=models.UniqueConstraint(
                fields=("playlist_item", "position"), name="unique_playlist_visual_position"
            ),
        ),
    ]
