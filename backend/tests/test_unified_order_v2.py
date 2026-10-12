"""Transactional delivery and acknowledgement of unified order revisions."""

from uuid import uuid4

import pytest
from django.db import transaction
from rest_framework.test import APIClient

from files.models import Playlist
from nomenclatures.models import StationCommandV2, StationCredential
from nomenclatures.player_v2.credentials import hash_station_token
from orders.models import Order, OrderStationState
from orders.services.unified_order_delivery import enqueue_order
from tasks.models import Task


@pytest.fixture
def order(nomenclature, user, monkeypatch):
    nomenclature.runtime_state = {"station_protocol": {"unified_orders_version": 1}}
    nomenclature.save(update_fields=["runtime_state"])
    playlist = Playlist.objects.create(name="Test playlist", owner=user)
    obj = Order.objects.create(name="Test order", owner=user, nomenclature=nomenclature,
                               playlist=playlist, placement="advertising", parameters={"times_in_hour": 1},
                               suppress_background_audio=True, suppress_background_visual=True)
    monkeypatch.setattr("orders.services.unified_order_delivery.build_task", lambda order: Task(
        owner=order.owner, client=order.nomenclature, type=4,
        parameters={"order_id": str(order.pk), "revision": order.revision}))
    monkeypatch.setattr("orders.services.unified_order_delivery._media_manifest", lambda order: [{
        "id": str(uuid4()), "sha256": "a" * 64, "hash": "a" * 96, "size": 1,
        "name": "Test", "url": "https://media.example.test/test.mp4"}])
    return obj


def sync(client, nomenclature, receipts):
    token = "test-order-station-token"
    StationCredential.objects.get_or_create(nomenclature=nomenclature, defaults={"token_hash": hash_station_token(token)})
    return client.post("/api/station/v2/sync/", {"receipts": receipts, "station_protocol": {"unified_orders_version": 1}}, content_type="application/json",
                       HTTP_AUTHORIZATION=f"Station {token}")


@pytest.mark.django_db
def test_order_and_command_roll_back_together(order):
    with pytest.raises(RuntimeError), transaction.atomic():
        enqueue_order(order)
        raise RuntimeError("rollback")
    assert not StationCommandV2.objects.exists()
    assert not OrderStationState.objects.exists()
    assert not Task.objects.exists()


@pytest.mark.django_db
def test_v2_delivery_does_not_also_create_a_legacy_task(client, order):
    command = enqueue_order(order)
    response = sync(client, order.nomenclature, [])
    assert response.status_code == 200
    assert response.json()["commands"][0]["command_id"] == str(command.command_id)
    assert not Task.objects.exists()
    state = OrderStationState.objects.get(order=order)
    assert state.status == "delivered"
    assert state.applied_revision is None


@pytest.mark.django_db
def test_apply_receipt_does_not_claim_order_is_on_air(client, order):
    command = enqueue_order(order)
    response = sync(client, order.nomenclature, [{"command_id": str(command.command_id), "status": "applied",
                                               "result": {"revision": 1, "files_verified": 1}}])
    assert response.status_code == 200
    state = OrderStationState.objects.get(order=order)
    assert state.status == "applied"
    assert state.applied_revision == 1
    assert state.on_air_revision is None
    order.refresh_from_db()
    assert order.status == 0


@pytest.mark.django_db
def test_cancel_endpoint_waits_for_matching_player_ack(client, super_user, order):
    previous = enqueue_order(order)
    api = APIClient()
    api.force_authenticate(super_user)
    response = api.post(f"/api/broadcast-orders/{order.pk}/cancel/")
    assert response.status_code == 200, response.data
    order.refresh_from_db()
    assert not order.is_active
    assert order.status != 3
    assert order.revision == 2
    previous.refresh_from_db()
    assert previous.status == "superseded"
    state = OrderStationState.objects.get(order=order)
    cancel_id = str(state.command_id)
    assert StationCommandV2.objects.get(command_id=cancel_id).kind == "cancel_order"
    assert api.post(f"/api/broadcast-orders/{order.pk}/cancel/").status_code == 200
    assert StationCommandV2.objects.count() == 2
    response = sync(client, order.nomenclature, [{"command_id": cancel_id, "status": "applied",
                                               "result": {"revision": 2, "cancelled": True}}])
    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == 3


@pytest.mark.django_db
@pytest.mark.parametrize("result", [{}, {"revision": True, "files_verified": 1}, {"revision": 1, "files_verified": True}])
def test_incomplete_ack_is_reported_as_failure(client, order, result):
    command = enqueue_order(order)
    assert sync(client, order.nomenclature, [{"command_id": str(command.command_id), "status": "applied", "result": result}]).status_code == 200
    state = OrderStationState.objects.get(order=order)
    assert state.status == "failed"
    assert state.applied_revision is None


@pytest.mark.django_db
def test_protocol_rejects_boolean_version(client, nomenclature):
    token = "protocol-test-token"
    StationCredential.objects.create(nomenclature=nomenclature, token_hash=hash_station_token(token))
    response = client.post("/api/station/v2/sync/", {"station_protocol": {"unified_orders_version": True}},
                           content_type="application/json", HTTP_AUTHORIZATION=f"Station {token}")
    assert response.status_code == 400


@pytest.mark.django_db
def test_downgraded_player_does_not_receive_unsupported_order_commands(client, order):
    command = enqueue_order(order)
    sync(client, order.nomenclature, [])
    response = client.post("/api/station/v2/sync/", {"receipts": []}, content_type="application/json",
                           HTTP_AUTHORIZATION="Station test-order-station-token")
    assert response.status_code == 200
    assert response.json()["commands"] == []
    order.nomenclature.refresh_from_db()
    assert order.nomenclature.player_sync_state.station_protocol == {}
    assert "station_protocol" not in (order.nomenclature.runtime_state or {})
    enqueue_order(order)
    assert not Task.objects.exists()
    command.refresh_from_db()
    assert command.status == "superseded"


@pytest.mark.django_db
def test_admin_add_form_uses_selected_stations_before_saving(order, super_user, rf):
    from django.contrib import admin
    from orders.unified_admin import OrderAdmin

    request = rf.get("/admin/orders/order/add/")
    request.user = super_user
    model_admin = OrderAdmin(Order, admin.site)
    form_class = model_admin.get_form(request)
    form = form_class(data={"name": "Admin order", "placement": "advertising", "playback_policy": "workday",
                            "target_nomenclatures": [str(order.nomenclature_id)], "playlist": str(order.playlist_id),
                            "owner": str(order.owner_id), "times_in_hour": "1",
                            "starts_at_0": "2026-10-01", "starts_at_1": "09:00:00", "ends_at_0": "2026-10-02", "ends_at_1": "18:00:00"})
    assert form.is_valid(), form.errors
    assert form.instance.nomenclature_id == order.nomenclature_id
    assert Order.objects.count() == 1


@pytest.mark.django_db
def test_admin_reports_invalid_delivery_as_form_error(order, super_user, rf, monkeypatch):
    from django.contrib import admin
    from django.core.exceptions import ValidationError
    from orders.unified_admin import OrderAdmin

    def invalid(_order):
        raise ValidationError("Missing media metadata")

    monkeypatch.setattr("orders.admin_forms.validate_order_delivery", invalid)
    request = rf.get("/admin/orders/order/add/")
    request.user = super_user
    form_class = OrderAdmin(Order, admin.site).get_form(request)
    form = form_class(data={"name": "Admin order", "placement": "advertising", "playback_policy": "workday",
                            "target_nomenclatures": [str(order.nomenclature_id)], "playlist": str(order.playlist_id),
                            "owner": str(order.owner_id), "times_in_hour": "1",
                            "starts_at_0": "2026-10-01", "starts_at_1": "09:00:00", "ends_at_0": "2026-10-02", "ends_at_1": "18:00:00"})
    assert not form.is_valid()
    assert "Missing media metadata" in str(form.non_field_errors())
    assert not StationCommandV2.objects.exists()


@pytest.mark.django_db
def test_cancelled_order_is_read_only_in_admin(order, super_user, rf):
    from django.contrib import admin
    from orders.unified_admin import OrderAdmin

    request = rf.get("/admin/orders/order/")
    request.user = super_user
    model_admin = OrderAdmin(Order, admin.site)
    assert model_admin.has_change_permission(request, order)
    order.is_active = False
    assert not model_admin.has_change_permission(request, order)


@pytest.mark.django_db
@pytest.mark.parametrize("policy", ["fixed_time", "fixed_to_close"])
def test_admin_preserves_fixed_schedule_start_time(order, super_user, rf, policy):
    from django.contrib import admin
    from orders.unified_admin import OrderAdmin

    request = rf.get("/admin/orders/order/add/")
    request.user = super_user
    form_class = OrderAdmin(Order, admin.site).get_form(request)
    form = form_class(data={
        "name": "Fixed admin order", "placement": "advertising", "playback_policy": policy,
        "target_nomenclatures": [str(order.nomenclature_id)], "playlist": str(order.playlist_id),
        "owner": str(order.owner_id), "times_in_hour": "4", "start_time": "10:00:00", "end_time": "18:00:00",
        "starts_at_0": "2026-10-01", "starts_at_1": "09:00:00", "ends_at_0": "2026-10-02", "ends_at_1": "18:00:00",
    })
    assert form.is_valid(), form.errors
    assert form.instance.parameters["start_time"] == "10:00:00"
    assert form.instance.parameters["times_in_hour"] == 4


@pytest.mark.django_db
@pytest.mark.parametrize("parameters", ['[]', '{"times_in_hour": true}', '{"times_in_hour": 4, "audio_muted": "true"}'])
def test_admin_ignores_injected_json_and_uses_typed_fields(order, super_user, rf, parameters):
    from django.contrib import admin
    from orders.unified_admin import OrderAdmin

    request = rf.get("/admin/orders/order/add/")
    request.user = super_user
    form_class = OrderAdmin(Order, admin.site).get_form(request)
    form = form_class(data={
        "name": "Invalid admin order", "placement": "advertising", "playback_policy": "workday",
        "target_nomenclatures": [str(order.nomenclature_id)], "playlist": str(order.playlist_id),
        "owner": str(order.owner_id), "parameters": parameters, "times_in_hour": "4",
        "starts_at_0": "2026-10-01", "starts_at_1": "09:00:00", "ends_at_0": "2026-10-02", "ends_at_1": "18:00:00",
    })
    assert form.is_valid(), form.errors
    assert "parameters" not in form.fields
    assert form.instance.parameters["times_in_hour"] == 4
    assert form.instance.parameters["audio_muted"] is False
    assert not StationCommandV2.objects.exists()


@pytest.mark.django_db
def test_cancel_new_options_order_reaches_player_after_capability_downgrade(client, super_user, order):
    order.nomenclature.runtime_state = {"station_protocol": {
        "unified_orders_version": 1, "advertising_options_version": 1,
    }}
    order.nomenclature.save(update_fields=["runtime_state"])
    order.suppress_background_audio = False
    order.save(update_fields=["suppress_background_audio"])
    command = enqueue_order(order)
    assert command.body["requires_advertising_options_version"] == 1
    # Downgrade before cancelling: old v1 must still receive the cancellation.
    assert sync(client, order.nomenclature, []).json()["commands"] == []
    api = APIClient()
    api.force_authenticate(super_user)
    response = api.post(f"/api/broadcast-orders/{order.pk}/cancel/")
    assert response.status_code == 200, response.data
    cancelled = sync(client, order.nomenclature, []).json()["commands"]
    assert len(cancelled) == 1
    assert cancelled[0]["kind"] == "cancel_order"
    assert cancelled[0]["task_type"] == 9
