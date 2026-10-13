# The new choice only affects Django's model state and admin/API validation.
# PostgreSQL has no enum or check constraint for this column, so no SQL is needed.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0005_order_unified"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="order",
                    name="playback_policy",
                    field=models.CharField(
                        choices=[
                            ("continuous", "Непрерывно"),
                            ("workday", "В рабочее время точки"),
                            ("hourly_slots", "Выходы в течение часа"),
                            ("fixed_time", "В заданные часы"),
                            ("open_offset", "От открытия со смещением"),
                            ("close_offset", "До закрытия со смещением"),
                            ("open_to_fixed", "От открытия до заданного времени"),
                            ("fixed_to_close", "От заданного времени до закрытия"),
                            ("start_to_close", "Реклама с указанного времени"),
                            ("event", "По событию"),
                        ],
                        default="workday",
                        max_length=16,
                        verbose_name="Правило воспроизведения",
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
