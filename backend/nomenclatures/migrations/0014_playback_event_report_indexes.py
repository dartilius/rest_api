from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("nomenclatures", "0013_playbackevent")]
    operations = [
        AddIndexConcurrently(
            model_name="playbackevent",
            index=models.Index(fields=("received_at",), name="player_event_received_idx"),
        ),
        AddIndexConcurrently(
            model_name="playbackevent",
            index=models.Index(fields=("occurred_at",), condition=models.Q(event_type="completed"), name="player_event_completed_idx"),
        ),
    ]
