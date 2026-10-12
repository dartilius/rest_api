"""Contracts for delivering unified orders to the currently released Player."""

from datetime import time, timedelta
from types import SimpleNamespace
from uuid import UUID

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.exceptions import ValidationError as DRFValidationError

from orders.models import Order
from orders.services.unified_order_delivery import build_task
from orders.unified_serializers import UnifiedOrderResendSerializer, UnifiedOrderSerializer


class _Task:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture(autouse=True)
def replace_task_model(monkeypatch):
    """Keep payload tests independent from the database model's FK checks."""
    monkeypatch.setattr("orders.services.unified_order_delivery.Task", _Task)


class _Items(list):
    def all(self):
        return self

    def select_related(self, *_fields):
        return self

    def prefetch_related(self, *_fields):
        return self

    def values_list(self, _field, *, flat):
        assert flat
        return [item.file.type for item in self]


class _Files(list):
    def all(self):
        return self

    def values_list(self, _field, *, flat):
        assert flat
        return [file.type for file in self]


def _file(identifier: str, media_type: int, file_hash: str):
    return SimpleNamespace(id=UUID(identifier), type=media_type, hash=file_hash)


def _order(*, placement: str, playback_policy: str, items: list, parameters=None, is_permanent=False):
    playlist = SimpleNamespace(
        id=UUID("00000000-0000-0000-0000-000000000010"),
        items=_Items(items),
        files=_Files(),
    )
    starts_at = timezone.now()
    return SimpleNamespace(
        id=UUID("00000000-0000-0000-0000-000000000100"),
        owner=SimpleNamespace(),
        nomenclature=SimpleNamespace(runtime_state={"station_protocol": {"advertising_options_version": 1}}),
        playlist=playlist,
        playlist_id=playlist.id,
        placement=placement,
        playback_policy=playback_policy,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(days=1),
        parameters=parameters or {},
        is_permanent=is_permanent,
        revision=1,
    )


def test_advertising_order_builds_legacy_task_with_structured_visuals():
    """A structured playlist remains consumable by the released Player."""
    audio = _file("00000000-0000-0000-0000-000000000001", 0, "audio-hash")
    image = _file("00000000-0000-0000-0000-000000000002", 2, "image-hash")
    item = SimpleNamespace(
        file=audio,
        file_id=audio.id,
        weight=35,
        visuals=_Items([SimpleNamespace(file=image, file_id=image.id)]),
    )
    order = _order(
        placement="advertising",
        playback_policy="workday",
        items=[item],
        parameters={"times_in_hour": 4, "weight": 70},
    )

    task = build_task(order)

    assert task.type == 4
    assert task.parameters["broadcast_type"] == 0
    assert task.parameters["order_parameters"] == {
        "times_in_hour": 4, "weight": 70, "suppress_background_audio": False,
        "suppress_background_visual": False, "audio_muted": False,
    }
    assert task.parameters["playlist"]["files"] == [
        {"id": str(audio.id), "hash": "audio-hash"}
    ]
    assert task.parameters["playlist"]["slides"] == {str(audio.id): [str(image.id)]}


def test_background_order_uses_existing_music_task_type():
    """A background order preserves the released Player's task-type contract."""
    music = _file("00000000-0000-0000-0000-000000000003", 0, "music-hash")
    item = SimpleNamespace(file=music, file_id=music.id, weight=100, visuals=_Items())
    order = _order(
        placement="background",
        playback_policy="workday",
        items=[item],
        is_permanent=True,
        parameters={"weight": 70, "image_duration": 12},
    )

    task = build_task(order)

    assert task.type == 0
    assert task.parameters["order_type"] == 0
    assert task.parameters["is_permanent"] is True
    assert task.parameters["parameters"] == {"weight": 70, "image_duration": 12}


@pytest.mark.parametrize("audio,visual,muted", [
    (False, False, False), (True, False, False), (False, True, True), (True, True, True),
])
def test_advertising_delivery_preserves_canonical_background_and_audio_flags(audio, visual, muted):
    media = _file("00000000-0000-0000-0000-000000000099", 1, "video-hash")
    order = _order(
        placement="advertising", playback_policy="workday",
        items=[SimpleNamespace(file=media, file_id=media.id, visuals=_Items())],
        parameters={"times_in_hour": 4, "audio_muted": muted,
                    "suppress_background_audio": not audio, "suppress_background_visual": not visual},
    )
    order.suppress_background_audio = audio
    order.suppress_background_visual = visual
    task = build_task(order)
    assert task.parameters["order_parameters"]["suppress_background_audio"] is audio
    assert task.parameters["order_parameters"]["suppress_background_visual"] is visual
    assert task.parameters["order_parameters"]["audio_muted"] is muted


def test_fixed_to_close_delivery_cannot_be_overridden_by_stale_schedule_mode():
    media = _file("00000000-0000-0000-0000-000000000098", 0, "audio-hash")
    order = _order(
        placement="advertising", playback_policy="fixed_to_close",
        items=[SimpleNamespace(file=media, file_id=media.id, visuals=_Items())],
        parameters={"times_in_hour": 4, "start_time": "10:00:00", "schedule_mode": "start_to_close"},
    )
    task = build_task(order)
    assert task.parameters["broadcast_type"] == 5
    assert "schedule_mode" not in task.parameters["order_parameters"]


@pytest.mark.parametrize("audio,visual,muted", [(False, True, False), (True, False, False), (True, True, True)])
def test_old_player_rejects_advertising_options_instead_of_silently_ignoring_them(audio, visual, muted):
    order = _order(placement="advertising", playback_policy="workday", items=[],
                   parameters={"times_in_hour": 4, "audio_muted": muted})
    order.nomenclature.runtime_state = {"station_protocol": {"unified_orders_version": 1}}
    order.suppress_background_audio = audio
    order.suppress_background_visual = visual
    with pytest.raises(ValidationError, match="Обновите Player"):
        build_task(order)


def test_legacy_normal_advertising_remains_deliverable_without_options_capability():
    media = _file("00000000-0000-0000-0000-000000000097", 0, "legacy-hash")
    order = _order(placement="advertising", playback_policy="workday",
                   items=[SimpleNamespace(file=media, file_id=media.id, visuals=_Items())],
                   parameters={"times_in_hour": 4})
    order.nomenclature.runtime_state = {"station_protocol": {"unified_orders_version": 1}}
    order.suppress_background_audio = True
    order.suppress_background_visual = True
    task = build_task(order)
    assert task.parameters["order_parameters"]["suppress_background_audio"] is True
    assert task.parameters["order_parameters"]["suppress_background_visual"] is True
    assert task.parameters["order_parameters"]["audio_muted"] is False


def test_hourly_slots_uses_the_released_player_workday_task_type():
    """The API-friendly hourly_slots name stays compatible with task type 4."""
    audio = _file("00000000-0000-0000-0000-000000000004", 0, "audio-hash")
    item = SimpleNamespace(file=audio, file_id=audio.id, weight=100, visuals=_Items())
    order = _order(
        placement="advertising",
        playback_policy="hourly_slots",
        items=[item],
        parameters={"times_in_hour": 6},
    )

    task = build_task(order)

    assert task.type == 4
    assert task.parameters["broadcast_type"] == 0


def test_advertising_from_selected_time_uses_existing_player_type_five():
    """The human-friendly policy stays compatible with the released Player."""
    audio = _file("00000000-0000-0000-0000-000000000005", 0, "audio-hash")
    item = SimpleNamespace(file=audio, file_id=audio.id, weight=100, visuals=_Items())
    order = _order(
        placement="advertising",
        playback_policy="start_to_close",
        items=[item],
        parameters={"times_in_hour": 4, "start_time": "09:07:30"},
    )

    task = build_task(order)

    assert task.type == 4
    assert task.parameters["broadcast_type"] == 5
    assert task.parameters["order_parameters"]["start_time"] == "09:07:30"
    assert task.parameters["order_parameters"]["schedule_mode"] == "start_to_close"


def test_continuous_policy_remains_unavailable_for_background():
    """Only advertising orders can replace the background continuously."""
    order = Order(placement="background", playback_policy="continuous")

    with pytest.raises(ValidationError, match="только рекламе"):
        order.clean()


def test_api_rejects_fixed_time_without_both_clock_boundaries():
    """Swagger's fixed-time example cannot be shortened into an ambiguous request."""
    serializer = UnifiedOrderSerializer()

    with pytest.raises(DRFValidationError, match="start_time"):
        serializer.validate({
            "placement": "advertising",
            "playback_policy": "fixed_time",
            "parameters": {"times_in_hour": 4, "end_time": "18:00:00"},
        })


def test_api_normalizes_hourly_slots_and_rejects_invalid_clock_format():
    """The external JSON contract is strict and still maps to the released Player."""
    serializer = UnifiedOrderSerializer()
    result = serializer.validate({
        "placement": "advertising",
        "playback_policy": "hourly_slots",
        "starts_at": timezone.now(),
        "ends_at": timezone.now() + timedelta(days=1),
        "parameters": {"times_in_hour": "8"},
    })
    assert result["parameters"] == {"times_in_hour": 8}

    with pytest.raises(DRFValidationError, match="HH:MM:SS"):
        serializer.validate({
            "placement": "advertising",
            "playback_policy": "open_offset",
            "parameters": {"times_in_hour": 4, "timedelta": "30 minutes"},
        })


def test_api_rejects_selected_time_outside_configured_workday():
    """A type-5 command cannot accidentally start advertising before opening."""
    serializer = UnifiedOrderSerializer()
    nomenclature = SimpleNamespace(worktime_start=time(9, 0), worktime_end=time(18, 0))

    with pytest.raises(DRFValidationError, match="рабочее время"):
        serializer.validate({
            "placement": "advertising",
            "playback_policy": "start_to_close",
            "nomenclature": nomenclature,
            "parameters": {"times_in_hour": 4, "start_time": "08:59:59"},
        })


def test_api_datetime_contract_has_no_timezone_suffix():
    """The new API always emits the Player's local timestamp format."""
    serializer = UnifiedOrderSerializer()
    rendered = serializer.fields["starts_at"].to_representation(
        timezone.now()
    )

    assert rendered is not None
    assert "+" not in rendered
    assert "T" not in rendered


def test_batch_resend_rejects_duplicate_order_identifiers():
    serializer = UnifiedOrderResendSerializer(
        data={
            "order_ids": [
                "00000000-0000-0000-0000-000000000101",
                "00000000-0000-0000-0000-000000000101",
            ]
        }
    )

    assert not serializer.is_valid()
    assert "order_ids" in serializer.errors
