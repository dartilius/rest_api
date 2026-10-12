"""Playback evidence, durable ACKs and factual counts through the real Station API."""

from uuid import uuid4
import json
from pathlib import Path

import pytest
from django.contrib import admin
from django.db import DatabaseError
from django.test import RequestFactory
from django.urls import reverse

from nomenclatures.models import StationCommandV2, StationCredential
from nomenclatures.player_v2.credentials import hash_station_token
from nomenclatures.player_v2.playback.admin import PlaybackEventAdmin
from nomenclatures.player_v2.playback.models import PlaybackEvent
from nomenclatures.player_v2.playback.service import completed_playbacks


pytestmark = pytest.mark.django_db


def test_actual_player_outbox_wire_is_accepted_and_each_media_counts_once(client, nomenclature, station_headers):
    fixture = json.loads((Path(__file__).parent / "fixtures" / "playback_events_v1.json").read_text(encoding="utf-8"))
    events = [{**event, "station_id": str(nomenclature.pk)} for event in fixture["events"]]
    response = _sync(client, station_headers, events)
    assert response.status_code == 200
    assert set(response.json()["playback_events_stored"]) == {event["event_id"] for event in events}
    assert response.json()["playback_event_errors"] == []
    assert PlaybackEvent.objects.count() == 16
    assert set(completed_playbacks().values_list("media_type", flat=True)) == {"music", "video", "image", "ad"}
    assert completed_playbacks().count() == 4
    assert _sync(client, station_headers, events).status_code == 200
    assert completed_playbacks().count() == 4


@pytest.fixture
def station_headers(nomenclature):
    token = "playback-events-test-token"
    StationCredential.objects.create(nomenclature=nomenclature, token_hash=hash_station_token(token))
    return {"HTTP_AUTHORIZATION": f"Station {token}"}


def _event(nomenclature, **overrides):
    return {
        "event_id": str(uuid4()), "station_id": str(nomenclature.pk),
        "playback_id": str(uuid4()), "event_sequence": 1, "event_type": "started",
        "occurred_at": "2026-10-05 09:00:00", "media_type": "video", "file_id": str(uuid4()),
        "order_id": None, "order_revision": None, "position_ms": 0, "duration_ms": 30_000,
        "reason": None, **overrides,
    }


def _next(event, kind, sequence, **overrides):
    return {**event, "event_id": str(uuid4()), "event_type": kind, "event_sequence": sequence, **overrides}


def _sync(client, headers, events):
    return client.post("/api/station/v2/sync/", data={"playback_events": events}, content_type="application/json", **headers)


def test_stored_ack_survives_response_loss_without_duplicate_rows(client, nomenclature, station_headers):
    event = _event(nomenclature)
    first = _sync(client, station_headers, [event])
    second = _sync(client, station_headers, [event])
    assert first.status_code == second.status_code == 200
    assert first.json()["playback_events_stored"] == second.json()["playback_events_stored"] == [event["event_id"]]
    assert first.json()["playback_event_storage"] == "postgresql"
    assert PlaybackEvent.objects.count() == 1
    assert PlaybackEvent.objects.get().payload == event


def test_event_id_conflict_does_not_overwrite_or_block_other_events(client, nomenclature, station_headers):
    original = _event(nomenclature)
    _sync(client, station_headers, [original])
    valid = _event(nomenclature)
    response = _sync(client, station_headers, [{**original, "position_ms": 99}, valid])
    assert response.status_code == 200
    assert response.json()["playback_events_stored"] == [valid["event_id"]]
    assert response.json()["playback_event_errors"] == [{"event_id": original["event_id"], "code": "event_conflict"}]
    assert PlaybackEvent.objects.get(event_id=original["event_id"]).position_ms == 0


def test_rebinding_cannot_reassign_queued_events_to_another_station(client, nomenclature, station_headers):
    event = _event(nomenclature, station_id=str(uuid4()))
    response = _sync(client, station_headers, [event])
    assert response.status_code == 200
    assert response.json()["playback_events_stored"] == []
    assert response.json()["playback_event_errors"][0]["code"] == "station_mismatch"
    assert not PlaybackEvent.objects.exists()


@pytest.mark.parametrize("kind", ["paused", "resumed", "interrupted", "error"])
def test_partial_or_failed_playback_never_counts_as_completed(client, nomenclature, station_headers, kind):
    started = _event(nomenclature)
    response = _sync(client, station_headers, [started, _next(started, kind, 2)])
    assert response.status_code == 200
    assert len(response.json()["playback_events_stored"]) == 2
    assert completed_playbacks().count() == 0


def test_completion_without_arrived_start_is_not_counted_until_start_is_stored(client, nomenclature, station_headers):
    started = _event(nomenclature)
    completed = _next(started, "completed", 2, position_ms=30_000)
    assert _sync(client, station_headers, [completed]).status_code == 200
    assert completed_playbacks().count() == 0
    assert _sync(client, station_headers, [started]).status_code == 200
    assert completed_playbacks().count() == 1


def test_repeated_completion_with_another_id_cannot_double_daily_count(client, nomenclature, station_headers):
    started = _event(nomenclature)
    completed = _next(started, "completed", 2)
    _sync(client, station_headers, [started, completed])
    response = _sync(client, station_headers, [_next(started, "completed", 3)])
    assert response.json()["playback_events_stored"] == []
    assert response.json()["playback_event_errors"][0]["code"] == "sequence_conflict"
    assert completed_playbacks().count() == 1


def test_event_sequence_reuse_is_rejected_even_with_another_event_id(client, nomenclature, station_headers):
    started = _event(nomenclature)
    _sync(client, station_headers, [started])
    response = _sync(client, station_headers, [{**started, "event_id": str(uuid4())}])
    assert response.json()["playback_events_stored"] == []
    assert response.json()["playback_event_errors"][0]["code"] == "sequence_conflict"


def test_session_identity_cannot_change_mid_playback(client, nomenclature, station_headers):
    started = _event(nomenclature)
    _sync(client, station_headers, [started])
    response = _sync(client, station_headers, [_next(started, "completed", 2, file_id=str(uuid4()))])
    assert response.json()["playback_event_errors"][0]["code"] == "event_conflict"
    assert completed_playbacks().count() == 0


def test_failed_start_is_recorded_without_inventing_a_started_event(client, nomenclature, station_headers):
    event = _event(nomenclature, event_type="error", reason="decoder_error")
    response = _sync(client, station_headers, [event])
    assert response.json()["playback_events_stored"] == [event["event_id"]]
    assert not PlaybackEvent.objects.filter(event_type="started").exists()


@pytest.mark.parametrize("changes", [
    {"event_sequence": True}, {"position_ms": 0.5}, {"duration_ms": -1},
    {"occurred_at": "2026-10-05T09:00:00Z"}, {"event_type": "completed"},
    {"order_id": str(uuid4()), "order_revision": None}, {"unexpected": 1},
])
def test_malformed_event_has_no_ack_or_partial_write(client, nomenclature, station_headers, changes):
    response = _sync(client, station_headers, [_event(nomenclature, **changes)])
    assert response.status_code == 400
    assert not PlaybackEvent.objects.exists()


def test_event_batch_is_bounded(client, nomenclature, station_headers):
    response = _sync(client, station_headers, [_event(nomenclature) for _ in range(101)])
    assert response.status_code == 400
    assert not PlaybackEvent.objects.exists()


def test_events_require_station_authentication(client, nomenclature):
    assert _sync(client, {}, [_event(nomenclature)]).status_code == 401
    assert not PlaybackEvent.objects.exists()


def test_database_failure_rolls_back_command_receipt_and_events(client, nomenclature, station_headers, monkeypatch):
    command = StationCommandV2.objects.create(nomenclature=nomenclature)
    def fail(*args, **kwargs):
        raise DatabaseError("test storage failure")
    monkeypatch.setattr(PlaybackEvent.objects, "create", fail)
    with pytest.raises(DatabaseError):
        client.post("/api/station/v2/sync/", data={
            "playback_events": [_event(nomenclature)],
            "receipts": [{"command_id": str(command.command_id), "status": "applied", "result": {}}],
        }, content_type="application/json", **station_headers)
    command.refresh_from_db()
    assert command.status == "pending"
    assert not PlaybackEvent.objects.exists()


def test_order_event_matches_delivered_revision_file_and_station(client, nomenclature, station_headers):
    order_id, file_id = str(uuid4()), str(uuid4())
    StationCommandV2.objects.create(nomenclature=nomenclature, kind="apply_order_manifest", body={
        "order_id": order_id, "revision": 2, "placement": "advertising", "files": [{"id": file_id}],
    }, status="applied")
    valid = _event(nomenclature, order_id=order_id, order_revision=2, file_id=file_id, media_type="ad")
    invalid = _event(nomenclature, order_id=order_id, order_revision=3, file_id=file_id, media_type="ad")
    response = _sync(client, station_headers, [valid, invalid])
    assert response.json()["playback_events_stored"] == [valid["event_id"]]
    assert response.json()["playback_event_errors"][0]["code"] == "order_mismatch"


def test_daily_admin_counts_only_complete_sessions_and_is_read_only(client, nomenclature, station_headers, django_user_model):
    started = _event(nomenclature)
    failed = _event(nomenclature)
    _sync(client, station_headers, [started, _next(started, "completed", 2), failed, _next(failed, "interrupted", 2)])
    user = django_user_model.objects.create_superuser(email="playback-report@example.test", password="test-password")
    client.force_login(user)
    response = client.get(reverse("admin:nomenclatures_playbackevent_daily"), {"day": "2026-10-05"})
    assert response.status_code == 200
    assert len(response.context_data["rows"]) == 1
    assert response.context_data["rows"][0]["completed_count"] == 1
    model_admin = PlaybackEventAdmin(PlaybackEvent, admin.site)
    request = RequestFactory().get("/")
    request.user = user
    assert not model_admin.has_add_permission(request)
    assert not model_admin.has_change_permission(request)
    assert not model_admin.has_delete_permission(request)
