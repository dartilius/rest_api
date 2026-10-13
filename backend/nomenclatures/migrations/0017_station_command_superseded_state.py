"""Record the existing superseded choice without changing database storage."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("nomenclatures", "0016_stationruntimesnapshot")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="stationcommandv2",
                    name="status",
                    field=models.CharField(
                        choices=[
                            ("pending", "Ожидает"),
                            ("superseded", "Заменена новой редакцией"),
                            ("applied", "Применена"),
                            ("failed", "Ошибка"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
            ],
        ),
    ]
