"""Progress is a fenced observation; only terminal receipts prove readiness."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.admin.sites import site
from django.test import RequestFactory
from django.utils import timezone

from files.models import Playlist
from nomenclatures.models import StationCommandV2, StationCredential
from nomenclatures.player_v2.credentials import hash_station_token
from nomenclatures.player_v2.serializers import StationV2SyncRequestSerializer
from orders.models import Order, OrderStationState
from orders.services.order_progress import delivery_progress, store_order_progress, with_order_progress
from orders.unified_serializers import UnifiedOrderSerializer


@pytest.fixture
def delivery(nomenclature, monkeypatch):
    playlist = Playlist.objects.create(name="Progress playlist")
    order = Order.objects.create(name="Progress order", placement="background", nomenclature=nomenclature, playlist=playlist)
    command = StationCommandV2.objects.create(nomenclature=nomenclature, kind="apply_order_manifest", body={
        "order_id": str(order.pk), "revision": 1, "files": [{"id": str(uuid4())}, {"id": str(uuid4())}],
    })
    state = OrderStationState.objects.create(order=order, nomenclature=nomenclature, command_id=command.command_id)
    credential = StationCredential.objects.create(nomenclature=nomenclature, token_hash=hash_station_token("progress-test-token"))
    monkeypatch.setattr("orders.services.unified_order_delivery.refresh_manifest_urls", lambda body: body)
    return order, command, state, credential


def report(command, **changes):
    return {"command_id": command.command_id, "revision": 1, "phase": "verifying",
            "files_verified": 1, "files_total": 2, **changes}


@pytest.mark.django_db
def test_progress_is_visible_without_claiming_ready_or_on_air(delivery, django_assert_num_queries):
    order, command, state, credential = delivery
    now = timezone.now()
    store_order_progress(credential, [report(command)], now)
    state.refresh_from_db()
    command.refresh_from_db()
    assert command.status == "pending"
    assert state.ready_revision is None and state.applied_revision is None and state.on_air_revision is None
    with django_assert_num_queries(1):
        rows = list(with_order_progress(Order.objects.select_related("station_state")))
        observation = delivery_progress(rows[0])
    assert observation["files_verified"] == 1 and observation["fresh"] is True
    assert "progress" in UnifiedOrderSerializer().get_delivery(rows[0])
    command.updated_at = now - timedelta(minutes=2)
    command.result["order_progress"]["received_at"] = command.updated_at.isoformat()
    command.save(update_fields=["result"])
    assert delivery_progress(order)["fresh"] is False


@pytest.mark.django_db
def test_late_observation_cannot_replace_newer_phase_and_heartbeat_is_coalesced(delivery):
    order, command, state, credential = delivery
    now = timezone.now()
    item = report(command, phase="applying", files_verified=2)
    store_order_progress(credential, [item], now)
    command.refresh_from_db()
    previous = command.result
    store_order_progress(credential, [report(command, phase="downloading", files_verified=0)], now - timedelta(seconds=1))
    command.refresh_from_db()
    assert command.result == previous
    store_order_progress(credential, [item], now + timedelta(seconds=1))
    command.refresh_from_db()
    assert command.result == previous
    store_order_progress(credential, [item], now + timedelta(seconds=15))
    command.refresh_from_db()
    assert command.result["order_progress"]["received_at"] == (now + timedelta(seconds=15)).isoformat()


@pytest.mark.django_db
@pytest.mark.parametrize("change", ["old_revision", "wrong_total", "foreign_station", "old_command", "terminal"])
def test_progress_cannot_update_an_unrelated_or_terminal_command(delivery, change):
    order, command, state, credential = delivery
    item = report(command)
    if change == "old_revision": item["revision"] = 2
    elif change == "wrong_total": item["files_total"] = 3
    elif change == "foreign_station": credential = type("OtherCredential", (), {"nomenclature_id": uuid4()})()
    elif change == "old_command":
        state.command_id = uuid4()
        state.save(update_fields=["command_id"])
    else:
        command.status = "applied"
        command.result = {"revision": 1, "files_verified": 2}
        command.save()
    previous = command.result
    store_order_progress(credential, [item], timezone.now())
    command.refresh_from_db()
    assert command.result == previous


@pytest.mark.django_db
def test_terminal_receipt_wins_over_progress_in_same_sync(delivery, client, django_capture_on_commit_callbacks):
    order, command, state, credential = delivery
    store_order_progress(credential, [report(command)], timezone.now())
    item = report(command)
    item["command_id"] = str(command.command_id)
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post("/api/station/v2/sync/", {
            "order_progress": [item], "receipts": [{"command_id": str(command.command_id), "status": "applied",
                "result": {"revision": 1, "files_verified": 2}}],
            "station_protocol": {"unified_orders_version": 1},
        }, content_type="application/json", HTTP_AUTHORIZATION="Station progress-test-token")
    assert response.status_code == 200
    command.refresh_from_db()
    state.refresh_from_db()
    assert command.result == {"revision": 1, "files_verified": 2}
    assert state.applied_revision == 1 and state.on_air_revision is None
    assert delivery_progress(order) is None


@pytest.mark.django_db
def test_sync_accepts_progress_and_admin_shows_verified_count(delivery, client, super_user, django_capture_on_commit_callbacks):
    order, command, state, credential = delivery
    item = report(command)
    item["command_id"] = str(command.command_id)
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post("/api/station/v2/sync/", {"order_progress": [item],
            "station_protocol": {"unified_orders_version": 1}}, content_type="application/json",
            HTTP_AUTHORIZATION="Station progress-test-token")
    assert response.status_code == 200
    request = RequestFactory().get("/admin/orders/order/")
    request.user = super_user
    model_admin = site._registry[Order]
    row = model_admin.get_queryset(request).get(pk=order.pk)
    assert "проверено файлов 1 из 2" in model_admin.delivery_state(row)


@pytest.mark.parametrize("changes", [{"files_verified": True}, {"revision": True}, {"files_total": 0},
    {"files_verified": 3}, {"phase": "ready"}, {"phase": "applying", "files_verified": 1},
    {"phase": "downloading", "files_verified": 1}])
def test_invalid_progress_does_not_pass_validation(changes):
    item = {"command_id": str(uuid4()), "revision": 1, "phase": "verifying", "files_verified": 1, "files_total": 2, **changes}
    assert not StationV2SyncRequestSerializer(data={"order_progress": [item]}).is_valid()
