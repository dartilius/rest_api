"""Advertising options require an explicit capability, cancellations remain safe."""

import pytest
from rest_framework.test import APIClient

from nomenclatures.models import StationCommandV2, StationCredential
from nomenclatures.player_v2.credentials import hash_station_token
from nomenclatures.player_v2.serializers import StationV2SyncRequestSerializer


@pytest.mark.parametrize("protocol", [
    {"unified_orders_version": 1},
    {"unified_orders_version": 1, "advertising_options_version": 1},
])
def test_station_protocol_keeps_old_v1_and_accepts_explicit_options_capability(protocol):
    serializer = StationV2SyncRequestSerializer(data={"station_protocol": protocol})
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["station_protocol"] == protocol


@pytest.mark.parametrize("value", [True, False, 0, 2, 1.0, "1", None])
def test_options_capability_requires_exact_integer_one(value):
    serializer = StationV2SyncRequestSerializer(data={"station_protocol": {
        "unified_orders_version": 1, "advertising_options_version": value,
    }})
    assert not serializer.is_valid()
    assert "station_protocol" in serializer.errors


@pytest.fixture
def station(nomenclature):
    token = "advertising-options-gate-station-token"
    StationCredential.objects.create(nomenclature=nomenclature, token_hash=hash_station_token(token))
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Station {token}")
    return client


def options_body(**options):
    return {"placement": "advertising", "task": {"task_type": 4, "parameters": {
        "order_parameters": options,
    }}}


@pytest.mark.django_db
@pytest.mark.parametrize("options", [
    {"suppress_background_audio": False, "suppress_background_visual": True},
    {"suppress_background_audio": True, "suppress_background_visual": False},
    {"suppress_background_audio": True, "suppress_background_visual": True, "audio_muted": True},
])
def test_old_v1_withholds_new_options_but_delivers_legacy_order_and_cancel(station, nomenclature, options):
    blocked = StationCommandV2.objects.create(nomenclature=nomenclature,
        kind="apply_order_manifest", body=options_body(**options))
    legacy = StationCommandV2.objects.create(nomenclature=nomenclature,
        kind="apply_order_manifest", body=options_body())
    compatible = StationCommandV2.objects.create(nomenclature=nomenclature,
        kind="apply_order_manifest", body=options_body(suppress_background_audio=True,
            suppress_background_visual=True, audio_muted=False))
    cancel = StationCommandV2.objects.create(nomenclature=nomenclature,
        kind="cancel_order", body={"requires_advertising_options_version": 1, "task_type": 9})
    response = station.post("/api/station/v2/sync/", {"station_protocol": {"unified_orders_version": 1}}, format="json")
    assert response.status_code == 200, response.data
    assert {item["command_id"] for item in response.data["commands"]} == {
        str(legacy.command_id), str(compatible.command_id), str(cancel.command_id),
    }
    blocked.refresh_from_db()
    assert blocked.status == "pending"
    assert blocked.delivered_at is None
    upgraded = station.post("/api/station/v2/sync/", {"station_protocol": {
        "unified_orders_version": 1, "advertising_options_version": 1,
    }}, format="json")
    assert upgraded.status_code == 200
    assert str(blocked.command_id) in {item["command_id"] for item in upgraded.data["commands"]}


@pytest.mark.django_db
def test_blocked_options_do_not_starve_compatible_commands_after_poll_limit(station, nomenclature):
    StationCommandV2.objects.bulk_create([
        StationCommandV2(nomenclature=nomenclature, kind="apply_order_manifest",
            body={"requires_advertising_options_version": 1}) for _ in range(101)
    ])
    legacy = StationCommandV2.objects.create(nomenclature=nomenclature,
        kind="apply_order_manifest", body=options_body())
    response = station.post("/api/station/v2/sync/", {"station_protocol": {"unified_orders_version": 1}}, format="json")
    assert response.status_code == 200
    assert [item["command_id"] for item in response.data["commands"]] == [str(legacy.command_id)]


@pytest.mark.django_db
def test_api_rejects_unsupported_options_atomically(nomenclature, user, super_user):
    from files.models import Playlist
    from orders.models import Order
    from tasks.models import Task

    nomenclature.runtime_state = {"station_protocol": {"unified_orders_version": 1}}
    nomenclature.save(update_fields=["runtime_state"])
    playlist = Playlist.objects.create(name="Options gate", owner=user)
    operator = APIClient()
    operator.force_authenticate(super_user)
    response = operator.post("/api/broadcast-orders/", {
        "name": "Unsupported options", "placement": "advertising", "playback_policy": "workday",
        "nomenclature": str(nomenclature.pk), "playlist": str(playlist.pk),
        "starts_at": "2026-10-01 09:00:00", "ends_at": "2026-10-02 18:00:00",
        "parameters": {"times_in_hour": 4},
        "suppress_background_audio": False, "suppress_background_visual": True,
    }, format="json")
    assert response.status_code == 400
    assert "Обновите Player" in str(response.data)
    assert not Order.objects.exists()
    assert not StationCommandV2.objects.exists()
    assert not Task.objects.exists()
