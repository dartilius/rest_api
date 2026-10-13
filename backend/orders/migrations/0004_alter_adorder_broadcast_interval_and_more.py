"""Preserve the production migration branch without repeating obsolete DDL.

Production generated this branch on 2026-09-18. Existing applied records remain
valid. New databases record its historical Django state only: tightening the
legacy range columns is obsolete and is superseded by the merge in 0008.
"""

import django.contrib.postgres.fields.ranges
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0003_bgorder_is_permanent_and_more")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="adorder", name="broadcast_interval",
                    field=django.contrib.postgres.fields.ranges.DateTimeRangeField(
                        blank=True, verbose_name="Интервал работы заказа",
                    ),
                ),
                migrations.AlterField(
                    model_name="bgorder", name="broadcast_interval",
                    field=django.contrib.postgres.fields.ranges.DateTimeRangeField(
                        blank=True, verbose_name="Интервал работы заказа",
                    ),
                ),
                migrations.AlterField(
                    model_name="bgorder", name="is_permanent",
                    field=models.BooleanField(
                        default=False, verbose_name="Бессрочный заказ",
                        help_text="Если включено — заказ не имеет даты окончания и используется как резервный плейлист. Играет, когда нет активных заказов с указанными датами.",
                    ),
                ),
            ],
        ),
    ]
