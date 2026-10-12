"""Player settings use the original field; playback presentation stays separate."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.admin.sites import site
from django.db import DatabaseError
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from nomenclatures.models import Nomenclature, StationCommandV2, StationCredential, StationSyncState
from nomenclatures.player_v2.credentials import hash_station_token
from nomenclatures.player_v2.sync_state import station_protocol
from nomenclatures.player_v2.views.sync import StationV2SyncView


@pytest.fixture
def station_headers(nomenclature):
    token = "settings-separation-test-token"
    StationCredential.objects.create(nomenclature=nomenclature, token_hash=hash_station_token(token))
    return {"HTTP_AUTHORIZATION": f"Station {token}"}


@pytest.mark.django_db
def test_sync_separates_settings_protocol_and_preserves_current_media(
    client, nomenclature, station_headers
):
    runtime = {"mode": "background", "background": [{"name": "Видео магазина"}]}
    Nomenclature.objects.filter(pk=nomenclature.pk).update(runtime_state=runtime)
    desired = deepcopy(nomenclature.settings)
    applied = deepcopy(desired)
    applied["mon"]["default_volume"][0] = 71
    protocol = {"unified_orders_version": 1, "background_visual_queue_version": 1}

    response = client.post("/api/station/v2/sync/", data={
        "applied_settings": applied, "applied_settings_revision": 4,
        "station_protocol": protocol,
    }, content_type="application/json", **station_headers)

    assert response.status_code == 200
    nomenclature.refresh_from_db()
    assert nomenclature.settings == applied
    assert nomenclature.runtime_state == runtime
    assert nomenclature.applied_settings_revision == 4
    assert nomenclature.player_sync_state.applied_settings is None
    assert station_protocol(nomenclature) == protocol


@pytest.mark.django_db
def test_existing_mixed_settings_are_moved_even_when_sync_omits_settings(
    client, nomenclature, station_headers
):
    protocol = {"unified_orders_version": 1}
    runtime = {"mode": "ad", "current_ad": {"name": "Ролик"},
               "applied_settings": nomenclature.settings,
               "applied_settings_revision": 4, "station_protocol": protocol}
    Nomenclature.objects.filter(pk=nomenclature.pk).update(runtime_state=runtime)

    response = client.post("/api/station/v2/sync/", data={}, content_type="application/json", **station_headers)

    assert response.status_code == 200
    nomenclature.refresh_from_db()
    assert nomenclature.runtime_state == {"mode": "ad", "current_ad": {"name": "Ролик"}}
    assert nomenclature.player_sync_state.applied_settings is None
    assert nomenclature.player_sync_state.station_protocol == {}
    assert nomenclature.applied_settings_revision == 4


@pytest.mark.django_db
def test_historical_shadow_is_consumed_and_new_report_wins(client, nomenclature, station_headers):
    old = deepcopy(nomenclature.settings)
    old["mon"]["default_volume"][0] = 15
    reported = deepcopy(nomenclature.settings)
    reported["mon"]["default_volume"][0] = 71
    StationSyncState.objects.create(nomenclature=nomenclature, applied_settings=old)

    response = client.post("/api/station/v2/sync/", data={
        "applied_settings": reported, "applied_settings_revision": 5,
    }, content_type="application/json", **station_headers)

    assert response.status_code == 200
    nomenclature.refresh_from_db()
    assert nomenclature.settings == reported
    assert nomenclature.player_sync_state.applied_settings is None


@pytest.mark.django_db
def test_settings_report_does_not_replace_pending_settings_command(client, nomenclature, station_headers):
    body = {"base_revision": 4, "operations": [{"day": "mon", "source": "music", "channel": "left", "value": 42}]}
    command = StationCommandV2.objects.create(nomenclature=nomenclature, kind="apply_settings_patch", body=body)

    response = client.post("/api/station/v2/sync/", data={
        "applied_settings": nomenclature.settings, "applied_settings_revision": 4,
    }, content_type="application/json", **station_headers)

    assert response.status_code == 200
    command.refresh_from_db()
    assert command.status == "pending"
    assert command.body == body
    assert any(item["command_id"] == str(command.command_id) for item in response.json()["commands"])


@pytest.mark.django_db
def test_replacing_live_snapshot_does_not_erase_player_protocol(nomenclature):
    StationSyncState.objects.create(
        nomenclature=nomenclature, applied_settings=nomenclature.settings,
        station_protocol={"unified_orders_version": 1, "continuous_advertising_version": 1},
    )
    Nomenclature.objects.filter(pk=nomenclature.pk).update(runtime_state={"mode": "idle"})
    nomenclature.refresh_from_db()
    assert station_protocol(nomenclature)["continuous_advertising_version"] == 1


@pytest.mark.django_db
def test_failed_sync_keeps_the_old_snapshot_and_rolls_back_the_move(
    client, nomenclature, station_headers, monkeypatch
):
    original = {"mode": "background", "applied_settings": nomenclature.settings,
                "station_protocol": {"unified_orders_version": 1}}
    Nomenclature.objects.filter(pk=nomenclature.pk).update(runtime_state=original)
    monkeypatch.setattr(
        "nomenclatures.player_v2.views.sync.store_playback_events",
        Mock(side_effect=DatabaseError("test rollback")),
    )
    with pytest.raises(DatabaseError):
        client.post("/api/station/v2/sync/", data={}, content_type="application/json", **station_headers)

    nomenclature.refresh_from_db()
    assert nomenclature.runtime_state == original
    assert not StationSyncState.objects.filter(nomenclature=nomenclature).exists()


@pytest.mark.django_db
def test_cleanup_does_not_overwrite_a_newer_legacy_broadcast_snapshot(nomenclature):
    stale = {"mode": "background", "background": [{"name": "Old"}],
             "applied_settings": nomenclature.settings}
    nomenclature.runtime_state = stale
    latest = {"mode": "background", "background": [{"name": "New"}]}
    Nomenclature.objects.filter(pk=nomenclature.pk).update(runtime_state=latest)

    StationV2SyncView._clean_runtime_sync_metadata(nomenclature)

    nomenclature.refresh_from_db()
    assert nomenclature.runtime_state == latest
    assert nomenclature.player_sync_state.applied_settings is None


@pytest.mark.django_db
def test_existing_sync_row_retains_legacy_confirmed_settings_when_missing(nomenclature):
    StationSyncState.objects.create(nomenclature=nomenclature)
    nomenclature.runtime_state = {"applied_settings": nomenclature.settings, "applied_settings_revision": 4}
    nomenclature.save(update_fields=["runtime_state"])

    StationV2SyncView._clean_runtime_sync_metadata(nomenclature)

    nomenclature.refresh_from_db()
    assert nomenclature.runtime_state == {}
    assert nomenclature.player_sync_state.applied_settings is None
    assert nomenclature.applied_settings_revision == 4


def test_live_display_excludes_settings_and_protocol_and_escapes_media_name():
    model_admin = site._registry[Nomenclature]
    obj = SimpleNamespace(runtime_state={
        "mode": "background", "background": [{"name": "<script>Video</script>"}],
        "applied_settings": {"mon": {"default_volume": [71]}},
        "station_protocol": {"unified_orders_version": 1},
    })

    displayed = str(model_admin.current_broadcast_state(obj))

    assert "Фоновый контент" in displayed
    assert "Video" in displayed
    assert "<script>" not in displayed
    assert "applied_settings" not in displayed
    assert "default_volume" not in displayed
    assert "station_protocol" not in displayed


@pytest.mark.django_db
def test_admin_card_keeps_original_settings_without_duplicate_or_music_statistics(
    client, nomenclature, super_user, monkeypatch
):
    applied = deepcopy(nomenclature.settings)
    applied["mon"]["default_volume"][0] = 71
    StationSyncState.objects.create(nomenclature=nomenclature, applied_settings=applied)
    Nomenclature.objects.filter(pk=nomenclature.pk).update(runtime_state={"mode": "background"})
    monkeypatch.setattr("nomenclatures.admin.get_station_presence", Mock(return_value={"status": "unknown", "last_seen": None}))
    client.force_login(super_user)

    response = client.get(reverse("admin:nomenclatures_nomenclature_change", args=[nomenclature.pk]))

    assert response.status_code == 200
    fieldsets = dict(response.context["adminform"].fieldsets)
    assert fieldsets["Текущее состояние эфира"]["fields"] == ("current_broadcast_state", "player_v2_connection")
    assert "settings" in fieldsets[None]["fields"]
    assert "Настройки вещания" not in fieldsets
    assert "runtime_state" not in response.context["adminform"].form.fields
    html = response.content.decode()
    assert "Подтверждённые Player настройки" not in html
    assert "music-stat-section" not in html
    # The separate statistics app remains in the navigation sidebar.
    assert reverse("admin:ch_statistic_musicstat_changelist") in html
    assert "stat-load-btn" not in html
    assert '<div class="broadcast-state">' in html
    assert "Фоновый контент" in html


@pytest.mark.django_db
def test_playback_presentation_does_not_add_a_separate_sql_query(nomenclature, super_user):
    StationSyncState.objects.create(nomenclature=nomenclature, applied_settings=nomenclature.settings)
    request = RequestFactory().get("/admin/nomenclatures/nomenclature/change/")
    request.user = super_user
    request.resolver_match = SimpleNamespace(url_name="nomenclatures_nomenclature_change")
    model_admin = site._registry[Nomenclature]

    with CaptureQueriesContext(connection) as queries:
        obj = model_admin.get_object(request, str(nomenclature.pk))
        settings = obj.settings
        playback = str(model_admin.current_broadcast_state(obj))

    assert len(queries) == 1
    assert settings == nomenclature.settings
    assert "default_volume" not in playback
