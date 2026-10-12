"""Input contracts shared by unified advertising orders and the Player."""

from datetime import UTC, datetime

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from orders.unified_serializers import UnifiedOrderSerializer


@pytest.mark.parametrize("value", [True, False, 1.5, 4.0, [], {}, None, 0, 61, "4.5"])
def test_advertising_rejects_non_integer_or_out_of_range_frequency(value):
    with pytest.raises(ValidationError) as error:
        UnifiedOrderSerializer().validate({
            "placement": "advertising", "playback_policy": "workday",
            "parameters": {"times_in_hour": value},
        })
    assert "parameters" in error.value.detail


@pytest.mark.parametrize("value", [[], [1], "", "parameters", 42, False, None])
def test_unified_order_parameters_must_be_object(value):
    with pytest.raises(ValidationError) as error:
        UnifiedOrderSerializer().validate({"placement": "background", "parameters": value})
    assert "parameters" in error.value.detail


@pytest.mark.parametrize("value", [True, 2.5, "50", -1, 101])
def test_unified_order_weight_matches_player_integer_contract(value):
    with pytest.raises(ValidationError) as error:
        UnifiedOrderSerializer().validate({"placement": "background", "parameters": {"weight": value}})
    assert "parameters" in error.value.detail


@pytest.mark.parametrize("value", [1, 0, "true", "false", None, []])
def test_order_audio_muted_requires_boolean(value):
    with pytest.raises(ValidationError) as error:
        UnifiedOrderSerializer().validate({"placement": "background", "parameters": {"audio_muted": value}})
    assert "parameters" in error.value.detail


@pytest.mark.parametrize("policy,extra", [
    ("workday", {}), ("hourly_slots", {}),
    ("open_offset", {"timedelta": "00:15:00"}),
    ("close_offset", {"timedelta": "00:10:00"}),
    ("fixed_time", {"start_time": "10:00:00", "end_time": "18:00:00"}),
    ("open_to_fixed", {"end_time": "18:00:00"}),
    ("fixed_to_close", {"start_time": "10:00:00"}),
    ("start_to_close", {"start_time": "09:07:30"}),
])
def test_supported_advertising_policies_preserve_valid_parameters(policy, extra):
    result = UnifiedOrderSerializer().validate({
        "placement": "advertising", "playback_policy": policy,
        "starts_at": datetime(2026, 10, 1, tzinfo=UTC),
        "ends_at": datetime(2026, 10, 2, tzinfo=UTC),
        "parameters": {"times_in_hour": "8", **extra},
    })
    assert result["parameters"] == {"times_in_hour": 8, **extra}


@pytest.mark.parametrize("missing", ["starts_at", "ends_at"])
def test_advertising_requires_explicit_period_boundaries(missing):
    data = {"placement": "advertising", "playback_policy": "workday",
            "parameters": {"times_in_hour": 4},
            "starts_at": datetime(2026, 10, 1, tzinfo=UTC),
            "ends_at": datetime(2026, 10, 2, tzinfo=UTC)}
    data[missing] = None
    with pytest.raises(ValidationError) as error:
        UnifiedOrderSerializer().validate(data)
    assert missing in error.value.detail


@pytest.mark.parametrize("end_time", ["09:00:00", "08:59:59"])
def test_fixed_time_rejects_empty_or_reversed_schedule(end_time):
    with pytest.raises(ValidationError) as error:
        UnifiedOrderSerializer().validate({
            "placement": "advertising", "playback_policy": "fixed_time",
            "parameters": {"times_in_hour": 4, "start_time": "09:00:00", "end_time": end_time},
        })
    assert "parameters" in error.value.detail


@pytest.mark.django_db
@pytest.mark.parametrize("missing", ["starts_at", "ends_at"])
def test_api_rejects_missing_advertising_dates_before_persisting_orders(
    nomenclature, user, super_user, missing
):
    from files.models import Playlist
    from nomenclatures.models import StationCommandV2
    from orders.models import Order
    from tasks.models import Task

    playlist = Playlist.objects.create(name="Date boundary playlist", owner=user)
    api = APIClient()
    api.force_authenticate(super_user)
    data = {"name": "Missing advertising boundary", "placement": "advertising",
            "playback_policy": "workday", "nomenclature": str(nomenclature.pk),
            "playlist": str(playlist.pk), "parameters": {"times_in_hour": 4},
            "starts_at": "2026-10-01 09:00:00", "ends_at": "2026-10-02 18:00:00"}
    del data[missing]
    response = api.post("/api/broadcast-orders/", data, format="json")
    assert response.status_code == 400
    assert missing in response.json()
    assert not Order.objects.exists()
    assert not Task.objects.exists()
    assert not StationCommandV2.objects.exists()
