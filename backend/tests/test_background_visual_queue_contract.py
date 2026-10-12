"""Mixed visual manifests and cancellation only after readiness acknowledgement."""

from unittest.mock import PropertyMock
import hashlib
import json
import os
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError as SerializerValidationError

from files.models import File, Playlist
from files.playlist_items import PlaylistItem
from nomenclatures.models import StationCommandV2, StationCredential
from nomenclatures.player_v2.credentials import hash_station_token
from nomenclatures.player_v2.serializers import StationV2SyncRequestSerializer
from orders.models import Order, OrderStationState
from orders.services.unified_order_delivery import build_task, enqueue_order
from orders.unified_serializers import UnifiedOrderSerializer
from orders.unified_admin import UnifiedOrderAdminForm


PROTOCOL = {"unified_orders_version": 1, "background_visual_queue_version": 1}


@pytest.fixture
def visual_order(nomenclature, user, monkeypatch):
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.example.test/visual"))
    nomenclature.runtime_state = {"station_protocol": PROTOCOL}
    nomenclature.save(update_fields=["runtime_state"])
    playlist = Playlist.objects.create(name="Mixed visual", owner=user)
    files = [File(name="Video.mp4", type=1, owner=user, source="test/video.mp4", size=1,
                  hash="a" * 96, sha256hash="a" * 64),
             File(name="Image.png", type=2, owner=user, source="test/image.png", size=1,
                  hash="b" * 96, sha256hash="b" * 64)]
    for file in files:
        body = f"visual-contract-{file.type}".encode()
        file.size = len(body)
        file.md5hash = hashlib.md5(body, usedforsecurity=False).hexdigest()
        file.sha256hash = hashlib.sha256(body).hexdigest()
        file.hash = file.md5hash + file.sha256hash
    File.objects.bulk_create(files)
    for index, file in enumerate(files):
        PlaylistItem.objects.create(playlist=playlist, file=file, position=index)
    return Order.objects.create(name="Visual", owner=user, nomenclature=nomenclature,
        playlist=playlist, placement="background", is_permanent=True,
        parameters={"weight": 70, "image_duration_seconds": 12})


@pytest.mark.django_db
def test_mixed_visual_payload_preserves_order_types_duration_and_weight(visual_order):
    task = build_task(visual_order)
    assert task.type == 1
    files = task.parameters["playlist"]["files"]
    assert [file["media_type"] for file in files] == [1, 2]
    assert "duration_seconds" not in files[0]
    assert files[1]["duration_seconds"] == 12
    assert task.parameters["parameters"]["weight"] == 70
    assert isinstance(task.parameters["broadcast_start"], str)
    assert task.parameters["parameters"]["permanent_generation"] == visual_order.created.isoformat(timespec="microseconds")


@pytest.mark.django_db
def test_mixed_visual_rejected_before_enqueue_for_old_player(visual_order):
    visual_order.nomenclature.runtime_state = {"station_protocol": {"unified_orders_version": 1}}
    with pytest.raises(ValidationError, match="Обновите Player"):
        enqueue_order(visual_order)
    assert not StationCommandV2.objects.exists()
    assert not OrderStationState.objects.exists()


@pytest.mark.django_db
def test_admin_unsaved_permanent_can_validate_before_created_timestamp(visual_order):
    preview = Order(name="New form", owner=visual_order.owner, nomenclature=visual_order.nomenclature,
        playlist=visual_order.playlist, placement="background", is_permanent=True)
    assert preview.created is None
    task = build_task(preview)
    assert task.type == 1
    assert "permanent_generation" not in task.parameters["parameters"]


@pytest.mark.django_db
def test_admin_controls_update_json_and_preserve_other_parameters(visual_order):
    visual_order.parameters = {"weight": 5, "image_duration_seconds": 30, "other": "kept"}
    visual_order.save(update_fields=["parameters"])
    form = UnifiedOrderAdminForm(instance=visual_order, data={
        "name": visual_order.name, "placement": "background", "playback_policy": "workday",
        "nomenclature": str(visual_order.nomenclature_id), "playlist": str(visual_order.playlist_id),
        "owner": str(visual_order.owner_id), "status": 0, "is_permanent": True,
        "order_weight": 70, "image_duration_seconds": 12,
    })
    assert form.is_valid(), form.errors
    assert form.save(commit=False).parameters == {"weight": 70, "image_duration_seconds": 12, "other": "kept"}


@pytest.mark.django_db
@pytest.mark.parametrize("only_image", [False, True])
def test_authenticated_mixed_visual_api_snapshot(visual_order, super_user, only_image):
    playlist = visual_order.playlist
    if only_image:
        playlist = Playlist.objects.create(name="Image only API", owner=super_user)
        image = visual_order.playlist.items.select_related("file").get(file__type=2).file
        PlaylistItem.objects.create(playlist=playlist, file=image, position=0)
    operator = APIClient()
    operator.force_authenticate(super_user)
    response = operator.post("/api/broadcast-orders/", {
        "name": "Mixed API", "placement": "background", "playback_policy": "workday",
        "nomenclature": str(visual_order.nomenclature_id), "playlist": str(playlist.pk),
        "is_permanent": True, "parameters": {"weight": 70, "image_duration_seconds": 12},
    }, format="json")
    assert response.status_code == 201, response.data
    token = "mixed-export-station-token"
    StationCredential.objects.create(nomenclature=visual_order.nomenclature, token_hash=hash_station_token(token))
    station = APIClient()
    station.credentials(HTTP_AUTHORIZATION=f"Station {token}")
    sync = station.post("/api/station/v2/sync/", {"station_protocol": PROTOCOL}, format="json")
    assert sync.status_code == 200, sync.data
    command = next(item for item in sync.json()["commands"] if item.get("order_id") == response.data["id"])
    assert [file["media_type"] for file in command["task"]["parameters"]["playlist"]["files"]] == ([2] if only_image else [1, 2])
    assert command["requires_background_visual_queue_version"] == 1
    cancelled = operator.post(f"/api/broadcast-orders/{response.data['id']}/cancel/", format="json")
    assert cancelled.status_code == 200, cancelled.data
    sync = station.post("/api/station/v2/sync/", {"station_protocol": PROTOCOL}, format="json")
    assert sync.status_code == 200, sync.data
    cancellation = next(item for item in sync.json()["commands"] if item.get("order_id") == response.data["id"])
    assert cancellation["kind"] == "cancel_order"
    output = os.environ.get("RMC_VISUAL_CONTRACT_OUTPUT")
    if output:
        bodies = {str(item.file_id): f"visual-contract-{item.file.type}"
                  for item in playlist.items.select_related("file")}
        target = Path(output)
        if only_image:
            target = target.with_name("permanent-image-contract.json")
        target.write_text(json.dumps({"apply": command, "cancel": cancellation, "bodies": bodies,
            "placement": "background", "expected_type": (2 if only_image else 1)}, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.mark.parametrize("value", [True, False, 0, -1, 86401, 1.0, "12", None])
def test_image_duration_rejects_invalid_values(value):
    serializer = UnifiedOrderSerializer()
    with pytest.raises(SerializerValidationError) as error:
        serializer.validate({"placement": "background", "parameters": {"image_duration_seconds": value}})
    assert "image_duration_seconds" in str(error.value)


@pytest.mark.parametrize("value", [True, False, 0, 2, 1.0, "1", None])
def test_visual_capability_requires_integer_one(value):
    serializer = StationV2SyncRequestSerializer(data={"station_protocol": {
        "unified_orders_version": 1, "background_visual_queue_version": value}})
    assert not serializer.is_valid()


@pytest.mark.django_db
@pytest.mark.parametrize("ready,status", [(True, "applied"), (False, "applied"), (True, "failed")])
def test_permanent_predecessor_cancel_waits_for_ready_apply_receipt(visual_order, ready, status):
    old_command = enqueue_order(visual_order)
    replacement = Order.objects.create(name="New visual", owner=visual_order.owner,
        nomenclature=visual_order.nomenclature, playlist=visual_order.playlist,
        placement="background", is_permanent=True, parameters={"weight": 50})
    command = enqueue_order(replacement)
    assert command.body["replaces_permanent_visual"] == [{"order_id": str(visual_order.pk), "revision": 1}]
    assert OrderStationState.objects.get(order=visual_order).desired_action == "apply"
    token = "visual-readiness-test-token"
    StationCredential.objects.create(nomenclature=visual_order.nomenclature, token_hash=hash_station_token(token))
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Station {token}")
    receipt = {"command_id": str(command.command_id), "status": status, "result": {
        "revision": 1, "files_verified": 2, "replacement_ready": ready, "replacement_group": "visual"}}
    response = client.post("/api/station/v2/sync/", {"station_protocol": PROTOCOL, "receipts": [receipt]}, format="json")
    assert response.status_code == 200, response.data
    state = OrderStationState.objects.get(order=visual_order)
    assert state.desired_action == ("cancel" if ready and status == "applied" else "apply")
    if ready and status == "applied":
        cancel = StationCommandV2.objects.get(command_id=state.command_id)
        assert cancel.kind == "cancel_order"
        assert cancel.body["task_type"] == 6
        assert cancel.body["revision"] == 2
        old_command.refresh_from_db()
        assert old_command.status == "superseded"
        assert Order.objects.get(pk=visual_order.pk).status != 3
        # Duplicate receipt cannot increment predecessor revision a second time.
        client.post("/api/station/v2/sync/", {"station_protocol": PROTOCOL, "receipts": [receipt]}, format="json")
        assert Order.objects.get(pk=visual_order.pk).revision == 2


@pytest.mark.django_db
def test_downgrade_withholds_visual_apply_without_blocking_cancel(visual_order):
    blocked = enqueue_order(visual_order)
    cancel = StationCommandV2.objects.create(nomenclature=visual_order.nomenclature, kind="cancel_order",
        body={"requires_background_visual_queue_version": 1, "task_type": 6})
    token = "visual-downgrade-test-token"
    StationCredential.objects.create(nomenclature=visual_order.nomenclature, token_hash=hash_station_token(token))
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Station {token}")
    response = client.post("/api/station/v2/sync/", {"station_protocol": {"unified_orders_version": 1}}, format="json")
    assert response.status_code == 200, response.data
    assert [item["command_id"] for item in response.data["commands"]] == [str(cancel.command_id)]
    blocked.refresh_from_db()
    assert blocked.delivered_at is None
