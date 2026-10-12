import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("nomenclatures", "0014_playback_event_report_indexes")]

    operations = [
        migrations.CreateModel(
            name="StationSyncState",
            fields=[
                ("nomenclature", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, serialize=False, related_name="player_sync_state",
                    to="nomenclatures.nomenclature",
                )),
                ("applied_settings", models.JSONField(blank=True, null=True)),
                ("station_protocol", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "station_player_sync_state",
                "verbose_name": "Подтверждённые настройки Player",
            },
        ),
    ]
