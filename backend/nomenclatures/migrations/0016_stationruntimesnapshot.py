import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("nomenclatures", "0015_stationsyncstate")]
    operations = [migrations.CreateModel(
        name="StationRuntimeSnapshot",
        fields=[
            ("nomenclature", models.OneToOneField(primary_key=True, serialize=False,
                related_name="live_runtime", on_delete=django.db.models.deletion.CASCADE,
                to="nomenclatures.nomenclature")),
            ("state", models.JSONField(default=dict)),
            ("actors", models.JSONField(default=dict)),
            ("received_at", models.DateTimeField()),
            ("transport", models.CharField(max_length=16)),
            ("frame_id", models.CharField(default="", max_length=96)),
        ],
        options={"db_table": "station_runtime_snapshot"},
    )]
