"""Last runtime snapshot; not an event journal or a statistic counter."""

from django.db import models


class StationRuntimeSnapshot(models.Model):
    nomenclature = models.OneToOneField(
        "nomenclatures.Nomenclature", primary_key=True, on_delete=models.CASCADE,
        related_name="live_runtime",
    )
    state = models.JSONField(default=dict)
    actors = models.JSONField(default=dict)
    received_at = models.DateTimeField()
    transport = models.CharField(max_length=16)
    frame_id = models.CharField(max_length=96, default="")

    class Meta:
        db_table = "station_runtime_snapshot"
