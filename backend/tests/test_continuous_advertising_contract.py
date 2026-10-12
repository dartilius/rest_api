"""Continuous advertising: validation, capability gates and real wire snapshots."""

import hashlib
import json
import os
from pathlib import Path
from unittest.mock import PropertyMock

import pytest
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as SerializerValidationError
from rest_framework.test import APIClient

from files.models import File, Playlist
from files.playlist_items import PlaylistItem
from nomenclatures.models import StationCommandV2, StationCredential
from nomenclatures.player_v2.credentials import hash_station_token
from nomenclatures.player_v2.serializers import StationV2SyncRequestSerializer
from orders.models import Order, OrderStationState
from orders.services.unified_order_delivery import build_task, enqueue_order
from orders.unified_admin import UnifiedOrderAdminForm
from orders.unified_serializers import UnifiedOrderSerializer
from tasks.models import Task


PROTOCOL = {
    "unified_orders_version": 1, "advertising_options_version": 1,
    "continuous_advertising_version": 1,
}


@pytest.fixture
def continuous_order(nomenclature, user, monkeypatch):
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.example.test/continuous"))
    nomenclature.runtime_state = {"station_protocol": PROTOCOL}
    nomenclature.save(update_fields=["runtime_state"])
    media_bytes = b"continuous-contract-video"
    md5 = hashlib.md5(media_bytes, usedforsecurity=False).hexdigest()
    sha256 = hashlib.sha256(media_bytes).hexdigest()
    media = File(name="Непрерывная реклама.mp4", type=1, owner=user,
                 source="contract/continuous.mp4", size=len(media_bytes),
                 md5hash=md5, sha256hash=sha256, hash=md5 + sha256)
    File.objects.bulk_create([media])
    playlist = Playlist.objects.create(name="Continuous", owner=user)
    PlaylistItem.objects.create(playlist=playlist, file=media, position=0)
    order = Order.objects.create(
        name="Continuous", owner=user, nomenclature=nomenclature, playlist=playlist,
        placement="advertising", playback_policy="continuous",
        starts_at="2026-10-01 09:00:00", ends_at="2026-10-03 18:00:00",
        parameters={"weight": 70},
    )
    order.refresh_from_db()
    return order


@pytest.fixture
def station(continuous_order):
    token = "continuous-contract-test-station"
    StationCredential.objects.create(
        nomenclature=continuous_order.nomenclature, token_hash=hash_station_token(token),
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Station {token}")
    return client


@pytest.mark.parametrize("muted", [False, True])
def test_continuous_validation_needs_no_frequency_and_normalizes_background_policy(muted):
    payload = {
        "placement": "advertising", "playback_policy": "continuous",
        "starts_at": "2026-10-01", "ends_at": "2026-10-03",
        "parameters": {"weight": 70, "audio_muted": muted, "times_in_hour": "ignored"},
        "suppress_background_audio": muted, "suppress_background_visual": False,
    }
    original_parameters = payload["parameters"]
    validated = UnifiedOrderSerializer().validate(payload)
    assert validated["parameters"] == {"weight": 70, "audio_muted": muted}
    assert validated["suppress_background_audio"] is not muted
    assert validated["suppress_background_visual"] is True
    assert original_parameters["times_in_hour"] == "ignored"


@pytest.mark.parametrize("missing", ["starts_at", "ends_at"])
def test_continuous_still_requires_both_date_bounds(missing):
    payload = {"placement": "advertising", "playback_policy": "continuous",
               "starts_at": "2026-10-01", "ends_at": "2026-10-03"}
    del payload[missing]
    with pytest.raises(SerializerValidationError) as exc:
        UnifiedOrderSerializer().validate(payload)
    assert missing in exc.value.detail


@pytest.mark.parametrize("value", [True, False, 0, 2, 1.0, "1", None])
def test_continuous_capability_requires_exact_integer_one(value):
    serializer = StationV2SyncRequestSerializer(data={"station_protocol": {
        "unified_orders_version": 1, "continuous_advertising_version": value,
    }})
    assert not serializer.is_valid()
    assert "station_protocol" in serializer.errors


def test_protocol_accepts_continuous_with_existing_capabilities():
    serializer = StationV2SyncRequestSerializer(data={"station_protocol": PROTOCOL})
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["station_protocol"] == PROTOCOL


@pytest.mark.django_db
@pytest.mark.parametrize("muted", [False, True])
def test_continuous_task_uses_type_seven_and_canonical_audio_policy(continuous_order, muted):
    continuous_order.parameters = {"audio_muted": muted, "times_in_hour": 60, "weight": 70}
    task = build_task(continuous_order)
    assert task.type == 4
    assert task.parameters["broadcast_type"] == 7
    assert task.parameters["order_parameters"] == {
        "audio_muted": muted, "weight": 70,
        "suppress_background_audio": not muted, "suppress_background_visual": True,
    }


@pytest.mark.django_db
@pytest.mark.parametrize("version", [None, True, 0, "1"])
def test_old_player_cannot_enqueue_continuous_atomically(continuous_order, version):
    continuous_order.nomenclature.runtime_state = {"station_protocol": {
        "unified_orders_version": 1, "continuous_advertising_version": version,
    }}
    with pytest.raises(ValidationError, match="Обновите Player"):
        enqueue_order(continuous_order)
    assert not StationCommandV2.objects.exists()
    assert not OrderStationState.objects.exists()
    assert not Task.objects.exists()


@pytest.mark.django_db
def test_ticker_cannot_enter_continuous_queue(continuous_order):
    File.objects.filter(
        pk=continuous_order.playlist.items.first().file_id,
    ).update(type=3)
    with pytest.raises(ValidationError, match="без тикеров"):
        enqueue_order(continuous_order)
    assert not StationCommandV2.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("marked", [False, True])
def test_downgrade_blocks_continuous_before_limit_but_keeps_cancel(station, continuous_order, marked):
    body = {"placement": "advertising", "task": {"parameters": {"broadcast_type": 7}}}
    if marked:
        body["requires_continuous_advertising_version"] = 1
    StationCommandV2.objects.bulk_create([
        StationCommandV2(nomenclature=continuous_order.nomenclature,
                         kind="apply_order_manifest", body=body) for _ in range(101)
    ])
    cancel = StationCommandV2.objects.create(
        nomenclature=continuous_order.nomenclature, kind="cancel_order", body=body,
    )
    ordinary = StationCommandV2.objects.create(
        nomenclature=continuous_order.nomenclature, kind="apply_order_manifest", body={},
    )
    response = station.post("/api/station/v2/sync/", {"station_protocol": {
        "unified_orders_version": 1, "advertising_options_version": 1,
    }}, format="json")
    assert response.status_code == 200, response.data
    assert {item["command_id"] for item in response.data["commands"]} == {
        str(cancel.command_id), str(ordinary.command_id),
    }


@pytest.mark.django_db
@pytest.mark.parametrize("muted", [False, True])
def test_admin_saves_continuous_without_frequency_and_canonical_suppression(continuous_order, muted):
    form = UnifiedOrderAdminForm(instance=continuous_order, data={
        "name": continuous_order.name, "placement": "advertising", "playback_policy": "continuous",
        "nomenclature": str(continuous_order.nomenclature_id), "playlist": str(continuous_order.playlist_id),
        "owner": str(continuous_order.owner_id), "status": 0,
        "starts_at": "2026-10-01 09:00:00", "ends_at": "2026-10-03 18:00:00",
        "parameters": json.dumps({"audio_muted": not muted, "weight": 70}),
        "advertising_audio": "muted" if muted else "sound",
    })
    assert form.is_valid(), form.errors
    saved = form.save()
    saved.refresh_from_db()
    assert saved.suppress_background_audio is not muted
    assert saved.suppress_background_visual is True
    assert saved.parameters["audio_muted"] is muted
    assert "times_in_hour" not in saved.parameters


@pytest.mark.django_db
def test_patch_policy_preserves_dates_and_clears_stale_frequency(continuous_order):
    continuous_order.playback_policy = "workday"
    continuous_order.parameters = {"times_in_hour": 4, "audio_muted": True}
    continuous_order.save(update_fields=["playback_policy", "parameters"])
    serializer = UnifiedOrderSerializer(instance=continuous_order, data={
        "playback_policy": "continuous",
    }, partial=True)
    assert serializer.is_valid(), serializer.errors
    updated = serializer.save()
    assert updated.parameters == {"audio_muted": True}
    assert updated.starts_at == continuous_order.starts_at
    assert updated.ends_at == continuous_order.ends_at
    assert updated.suppress_background_audio is False
    assert updated.suppress_background_visual is True


@pytest.mark.django_db
def test_api_rejects_old_station_without_persisting_order_or_command(continuous_order, super_user):
    nomenclature = continuous_order.nomenclature
    nomenclature.runtime_state = {"station_protocol": {"unified_orders_version": 1}}
    nomenclature.save(update_fields=["runtime_state"])
    operator = APIClient()
    operator.force_authenticate(super_user)
    response = operator.post("/api/broadcast-orders/", {
        "name": "Unsupported continuous", "placement": "advertising", "playback_policy": "continuous",
        "nomenclature": str(nomenclature.pk), "playlist": str(continuous_order.playlist_id),
        "starts_at": "2026-10-01 09:00:00", "ends_at": "2026-10-03 18:00:00",
    }, format="json")
    assert response.status_code == 400, response.data
    assert "Обновите Player" in str(response.data)
    assert list(Order.objects.values_list("id", flat=True)) == [continuous_order.pk]
    assert not StationCommandV2.objects.exists()
    assert not OrderStationState.objects.exists()
    assert not Task.objects.exists()


@pytest.mark.django_db
def test_authenticated_continuous_wire_snapshots(continuous_order, station, super_user):
    """Export six actual API responses for Player HTTP/hash/SQLite contract tests."""
    operator = APIClient()
    operator.force_authenticate(super_user)
    contracts = []
    media = continuous_order.playlist.items.first().file
    for media_type in (0, 1, 2):
        extension = {0: "mp3", 1: "mp4", 2: "png"}[media_type]
        File.objects.filter(pk=media.pk).update(
            type=media_type, name=f"Непрерывная реклама.{extension}",
            source=f"contract/continuous.{extension}",
        )
        for muted in (False, True):
            upgraded = station.post("/api/station/v2/sync/", {
                "station_protocol": PROTOCOL,
            }, format="json")
            assert upgraded.status_code == 200, upgraded.data
            payload = {
                "name": f"Continuous {media_type}/{muted}", "placement": "advertising",
                "playback_policy": "continuous", "nomenclature": str(continuous_order.nomenclature_id),
                "playlist": str(continuous_order.playlist_id),
                "starts_at": "2026-10-01 09:00:00", "ends_at": "2026-10-03 18:00:00",
                "parameters": {"audio_muted": muted, "weight": 70, "image_duration_seconds": 12},
                "suppress_background_audio": muted, "suppress_background_visual": False,
            }
            response = operator.post("/api/broadcast-orders/", payload, format="json")
            assert response.status_code == 201, response.data
            order_id = response.data["id"]
            assert response.data["suppress_background_audio"] is not muted
            assert response.data["suppress_background_visual"] is True
            sync = station.post("/api/station/v2/sync/", {"station_protocol": PROTOCOL}, format="json")
            assert sync.status_code == 200, sync.data
            command = next(item for item in sync.json()["commands"] if item.get("order_id") == order_id)
            assert command["requires_continuous_advertising_version"] == 1
            assert command["task"]["parameters"]["broadcast_type"] == 7
            assert "times_in_hour" not in command["task"]["parameters"]["order_parameters"]
            assert command["task"]["parameters"]["order_parameters"]["audio_muted"] is muted
            result = {"revision": command["revision"], "files_verified": len(command["files"])}
            ack = {"command_id": command["command_id"], "status": "applied", "result": result}
            for _ in range(2):
                accepted = station.post("/api/station/v2/sync/", {
                    "station_protocol": PROTOCOL, "receipts": [ack],
                }, format="json")
                assert accepted.status_code == 200, accepted.data
            state = OrderStationState.objects.get(order_id=order_id)
            assert state.applied_revision == command["revision"]
            assert state.status == "applied"
            cancelled = operator.post(f"/api/broadcast-orders/{order_id}/cancel/", format="json")
            assert cancelled.status_code == 200, cancelled.data
            sync = station.post("/api/station/v2/sync/", {"station_protocol": PROTOCOL}, format="json")
            cancellation = next(item for item in sync.json()["commands"] if item.get("order_id") == order_id)
            assert cancellation["kind"] == "cancel_order"
            assert cancellation["revision"] == command["revision"] + 1
            cancelled_ack = station.post("/api/station/v2/sync/", {
                "station_protocol": {"unified_orders_version": 1},
                "receipts": [{"command_id": cancellation["command_id"], "status": "applied",
                              "result": {"revision": cancellation["revision"], "cancelled": True}}],
            }, format="json")
            assert cancelled_ack.status_code == 200, cancelled_ack.data
            assert Order.objects.get(pk=order_id).status == 3
            contracts.append({
                "policy": "continuous", "placement": "advertising", "expected_type": 7,
                "media_type": media_type, "audio_muted": muted,
                "apply": command, "cancel": cancellation,
                "bodies": {str(media.pk): "continuous-contract-video"},
            })
    output = os.environ.get("RMC_CONTINUOUS_CONTRACT_OUTPUT")
    if output:
        Path(output).write_text(json.dumps(contracts, ensure_ascii=False, indent=2), encoding="utf-8")
