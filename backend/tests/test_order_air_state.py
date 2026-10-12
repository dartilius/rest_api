"""Current radio status needs exact revision, confirmed start and a fresh snapshot."""

from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.contrib.admin.sites import site
from django.utils import timezone

from files.models import Playlist
from nomenclatures.models import StationCommandV2, StationCredential
from nomenclatures.player_v2.credentials import hash_station_token
from nomenclatures.player_v2.playback.serializers import PlaybackEventSerializer
from nomenclatures.player_v2.playback.service import store_playback_events
from orders.models import Order, OrderStationState
from orders.services.order_air_state import actual_order_state, confirm_on_air_revisions


def objects():
    delivery = SimpleNamespace(status="applied", desired_action="apply", applied_revision=2,
                               desired_revision=2, on_air_revision=2, last_error="")
    order = SimpleNamespace(pk=uuid4(), nomenclature_id=uuid4(), revision=2, status=0, station_state=delivery)
    snapshot = {"received_at": timezone.now().isoformat(), "transport": "websocket", "state": {
        "mode": "music", "maintenance_mode": False, "current_ad": None, "background": [
            {"order_id": str(order.pk), "order_revision": 2, "status": "играет"},
        ],
    }}
    return order, snapshot


def test_on_air_and_pause_are_actual_not_delivery_statuses():
    order, snapshot = objects()
    assert actual_order_state(order, snapshot)["code"] == "on_air"
    snapshot["state"]["background"][0]["status"] = "пауза"
    assert actual_order_state(order, snapshot)["code"] == "paused"
    assert order.station_state.status == "applied"


@pytest.mark.parametrize("change", ["old_revision", "no_revision", "stale", "legacy"])
def test_old_or_unbound_snapshot_never_proves_current_order_playing(change):
    order, snapshot = objects()
    if change == "old_revision": snapshot["state"]["background"][0]["order_revision"] = 1
    elif change == "no_revision": snapshot["state"]["background"][0].pop("order_revision")
    elif change == "stale": snapshot["received_at"] = (timezone.now() - timedelta(minutes=2)).isoformat()
    else: snapshot["transport"] = "legacy"
    assert actual_order_state(order, snapshot)["code"] == "unknown"


def test_applied_without_real_start_is_not_on_air():
    order, snapshot = objects()
    order.station_state.on_air_revision = None
    assert actual_order_state(order, snapshot)["code"] == "awaiting_fact"
    snapshot["state"]["background"] = []
    assert actual_order_state(order, snapshot)["code"] == "off_air"


def test_cancellation_and_failure_are_not_disguised_as_on_air():
    order, snapshot = objects()
    order.station_state.desired_action = "cancel"
    assert actual_order_state(order, snapshot)["code"] == "cancelling"
    order.station_state.status = "cancelled"
    assert actual_order_state(order, snapshot)["code"] == "cancelled"
    order.station_state.desired_action = "apply"
    order.station_state.status = "failed"
    assert actual_order_state(order, snapshot)["code"] == "delivery_error"


@pytest.mark.django_db
def test_committed_start_projects_only_exact_applied_revision(nomenclature, django_capture_on_commit_callbacks):
    playlist = Playlist.objects.create(name="Air status playlist")
    order = Order.objects.create(name="Air status order", placement="background", nomenclature=nomenclature, playlist=playlist)
    state = OrderStationState.objects.create(order=order, nomenclature=nomenclature,
        desired_revision=1, applied_revision=1, status="applied")
    token = "air-state-token"
    credential = StationCredential.objects.create(nomenclature=nomenclature, token_hash=hash_station_token(token))
    file_id = uuid4()
    StationCommandV2.objects.create(nomenclature=nomenclature, kind="apply_order_manifest", body={
        "order_id": str(order.pk), "revision": 1, "placement": "background", "files": [{"id": str(file_id)}],
    })
    wire = {"event_id": str(uuid4()), "station_id": str(nomenclature.pk), "playback_id": str(uuid4()),
            "event_sequence": 1, "event_type": "started", "occurred_at": "2026-10-06 09:00:00",
            "media_type": "video", "file_id": str(file_id), "order_id": str(order.pk), "order_revision": 1,
            "position_ms": 0, "duration_ms": 30000, "reason": None}
    serializer = PlaybackEventSerializer(data=wire)
    serializer.is_valid(raise_exception=True)
    with django_capture_on_commit_callbacks(execute=True):
        stored, errors = store_playback_events(credential, [serializer.validated_data])
    assert not errors and stored == [wire["event_id"]]
    state.refresh_from_db()
    assert state.on_air_revision == 1
    state.desired_revision = 2
    state.applied_revision = 2
    state.on_air_revision = None
    state.save()
    Order.objects.filter(pk=order.pk).update(revision=2)
    confirm_on_air_revisions([order.pk])
    state.refresh_from_db()
    assert state.on_air_revision is None


@pytest.mark.django_db
def test_inactive_cancelled_orders_remain_in_admin_history(nomenclature, super_user):
    from django.test import RequestFactory
    playlist = Playlist.objects.create(name="Cancelled playlist")
    order = Order.objects.create(name="Cancelled order", placement="background", nomenclature=nomenclature,
                                 playlist=playlist, status=3, is_active=False)
    request = RequestFactory().get("/admin/orders/order/")
    request.user = super_user
    assert site._registry[Order].get_queryset(request).filter(pk=order.pk).exists()
