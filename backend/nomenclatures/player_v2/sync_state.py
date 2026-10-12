"""Confirmed settings and protocol metadata, separate from the live broadcast."""

from django.db import models


class StationSyncState(models.Model):
    nomenclature = models.OneToOneField(
        "nomenclatures.Nomenclature", primary_key=True, on_delete=models.CASCADE,
        related_name="player_sync_state",
    )
    # Compatibility with 0015's first version. On sync, an old snapshot is
    # consumed into Nomenclature.settings and this column is cleared.
    applied_settings = models.JSONField(null=True, blank=True)
    station_protocol = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "station_player_sync_state"
        verbose_name = "Подтверждённые настройки Player"


def station_protocol(station):
    state = getattr(station, "player_sync_state", None)
    if state is not None:
        protocol = state.station_protocol
    else:
        runtime = getattr(station, "runtime_state", None)
        protocol = runtime.get("station_protocol", {}) if isinstance(runtime, dict) else {}
    return protocol if isinstance(protocol, dict) else {}
