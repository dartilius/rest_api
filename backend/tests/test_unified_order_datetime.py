"""Local timestamps and optional end dates in the unified order API/schema."""

from datetime import datetime
import re

import pytest
from django.urls import path
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APIClient

from files.models import Playlist
from orders.models import Order
from orders.unified_views import UnifiedOrderViewSet


@pytest.fixture
def order(nomenclature, user, monkeypatch):
    """Delivery is covered separately; these tests exercise HTTP dates and validation."""
    playlist = Playlist.objects.create(name="Dates test playlist", owner=user)
    obj = Order.objects.create(name="Dates test order", owner=user, nomenclature=nomenclature,
                               playlist=playlist, placement="advertising", parameters={"times_in_hour": 4})
    monkeypatch.setattr("orders.unified_views.enqueue_order", lambda _order: None)
    return obj


@pytest.mark.django_db
@pytest.mark.parametrize("placement,permanent", [("advertising", False), ("background", True)])
def test_create_response_uses_local_dates_and_permanent_background_needs_no_end(
    order, super_user, placement, permanent,
):
    api = APIClient()
    api.force_authenticate(super_user)
    payload = {"name": "Local dates", "placement": placement, "playback_policy": "workday",
               "nomenclature": str(order.nomenclature_id), "playlist": str(order.playlist_id),
               "starts_at": "2026-09-30 13:04:00", "is_permanent": permanent,
               "parameters": {"times_in_hour": 4} if placement == "advertising" else {}}
    if not permanent:
        payload["ends_at"] = "2026-10-09 13:04:00"
    response = api.post("/api/broadcast-orders/", payload, format="json")
    assert response.status_code == 201, response.data
    data = response.json()
    assert data["starts_at"] == "2026-09-30 13:04:00"
    assert data["ends_at"] == payload.get("ends_at")
    for name in ("created", "starts_at", "ends_at"):
        assert data[name] is None or re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", data[name])


@pytest.mark.django_db
def test_switch_to_permanent_background_clears_previous_end_if_omitted(order, super_user):
    order.placement = "background"
    order.ends_at = datetime(2026, 10, 9, 13, 4)
    order.save(update_fields=("placement", "ends_at"))
    api = APIClient()
    api.force_authenticate(super_user)
    response = api.patch(f"/api/broadcast-orders/{order.pk}/", {"is_permanent": True}, format="json")
    assert response.status_code == 200, response.data
    assert response.json()["ends_at"] is None
    order.refresh_from_db()
    assert order.is_permanent
    assert order.ends_at is None


@pytest.mark.django_db
def test_explicit_end_is_rejected_for_permanent_background(order, super_user):
    order.placement = "background"
    order.save(update_fields=("placement",))
    api = APIClient()
    api.force_authenticate(super_user)
    response = api.patch(f"/api/broadcast-orders/{order.pk}/",
                         {"is_permanent": True, "ends_at": "2026-10-09 13:04:00"}, format="json")
    assert response.status_code == 400
    assert "ends_at" in response.json()
    order.refresh_from_db()
    assert not order.is_permanent


def test_openapi_examples_match_local_timestamp_contract():
    schema = SchemaGenerator(patterns=[path("api/broadcast-orders/", UnifiedOrderViewSet.as_view({"post": "create"}))]).get_schema(public=True)
    components = [value for name, value in schema["components"]["schemas"].items() if name.startswith("UnifiedOrder")]
    assert components
    for component in components:
        for name in ("starts_at", "ends_at", "created"):
            field = component.get("properties", {}).get(name)
            if field is not None:
                assert field["type"] == "string"
                assert "format" not in field
                assert field["example"] == "2026-09-30 13:04:00"
        assert "ends_at" not in component.get("required", [])
    response = schema["paths"]["/api/broadcast-orders/"]["post"]["responses"]["201"]["content"]["application/json"]
    examples = [item["value"] for item in response["examples"].values()]
    assert any(item["is_permanent"] and item["ends_at"] is None for item in examples)
    for item in examples:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", item["created"])
