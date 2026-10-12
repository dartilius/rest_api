"""Export real authenticated sync responses for the companion Player tests.

The optional output is an integration artifact, not a substitute for assertions.
Media storage URLs are the only external backend dependency replaced here.
"""

import hashlib
import json
import os
from pathlib import Path
from unittest.mock import PropertyMock

import pytest
from rest_framework.test import APIClient

from files.models import File, Playlist
from files.playlist_items import PlaylistItem, PlaylistItemVisual
from nomenclatures.models import StationCredential
from nomenclatures.player_v2.credentials import hash_station_token


CASES = [
    ("workday", {"times_in_hour": 4}, 0),
    ("hourly_slots", {"times_in_hour": 8}, 0),
    ("open_offset", {"times_in_hour": 4, "timedelta": "00:05:30"}, 1),
    ("close_offset", {"times_in_hour": 4, "timedelta": "00:05:30"}, 2),
    ("fixed_time", {"times_in_hour": 4, "start_time": "10:00:00", "end_time": "16:00:00"}, 3),
    ("open_to_fixed", {"times_in_hour": 4, "end_time": "16:00:00"}, 4),
    ("fixed_to_close", {"times_in_hour": 4, "start_time": "10:00:00"}, 5),
    ("start_to_close", {"times_in_hour": 4, "start_time": "10:00:00"}, 5),
]


@pytest.mark.django_db
def test_authenticated_orders_produce_player_consumable_snapshots(
    nomenclature, super_user, monkeypatch,
):
    token = "contract-station-token"
    StationCredential.objects.create(
        nomenclature=nomenclature, token_hash=hash_station_token(token),
    )
    station = APIClient()
    station.credentials(HTTP_AUTHORIZATION=f"Station {token}")
    protocol = {"unified_orders_version": 1, "advertising_options_version": 1,
                "background_visual_queue_version": 1}
    assert station.post("/api/station/v2/sync/", {"station_protocol": protocol}, format="json").status_code == 200
    operator = APIClient()
    operator.force_authenticate(super_user)
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.example.test/contract"))
    contracts = []

    scenarios = [(policy, params, expected, "advertising", 0) for policy, params, expected in CASES]
    scenarios += [("workday", {}, media_type, "background", media_type) for media_type in range(4)]
    scenarios += [
        ("workday", {"times_in_hour": 4, "audio_muted": True}, 0, "advertising", 1),
        ("workday", {"times_in_hour": 4}, 0, "advertising", 0),
        ("workday", {"times_in_hour": 4}, 0, "advertising", 2),
    ]
    for index, (policy, params, expected_type, placement, media_type) in enumerate(scenarios):
        body = f"contract-media-{index}".encode()
        digest = hashlib.sha256(body).hexdigest()
        md5 = hashlib.md5(body, usedforsecurity=False).hexdigest()
        extension = {0: "mp3", 1: "mp4", 2: "png", 3: "txt"}[media_type]
        media = File(name=f"Контент {index}.{extension}", type=media_type, owner=super_user,
                     source=f"contract/{index}.{extension}", size=len(body),
                     md5hash=md5, sha256hash=digest, hash=md5 + digest)
        # Bypass ingestion only: fixture bytes already have verified metadata.
        File.objects.bulk_create([media])
        playlist = Playlist.objects.create(name=f"Contract {index}", owner=super_user)
        item = PlaylistItem.objects.create(playlist=playlist, file=media, position=0)
        bodies = {str(media.pk): body.decode()}
        if placement == "advertising" and index < 8:
            image_body = f"contract-slide-{index}".encode()
            image_sha = hashlib.sha256(image_body).hexdigest()
            image_md5 = hashlib.md5(image_body, usedforsecurity=False).hexdigest()
            image = File(name=f"Слайд {index}.png", type=2, owner=super_user,
                         source=f"contract/slide-{index}.png", size=len(image_body),
                         md5hash=image_md5, sha256hash=image_sha, hash=image_md5 + image_sha)
            File.objects.bulk_create([image])
            PlaylistItemVisual.objects.create(playlist_item=item, file=image, position=0)
            bodies[str(image.pk)] = image_body.decode()
        payload = {
            "name": f"Contract {index}", "placement": placement, "playback_policy": policy,
            "nomenclature": str(nomenclature.pk), "playlist": str(playlist.pk),
            "starts_at": "2026-10-01 08:00:00", "ends_at": "2026-10-03 21:00:00",
            "parameters": {**params, "weight": 70},
            "suppress_background_audio": not params.get("audio_muted", False),
            "suppress_background_visual": True,
        }
        response = operator.post("/api/broadcast-orders/", payload, format="json")
        assert response.status_code == 201, response.data
        order_id = response.data["id"]
        sync = station.post("/api/station/v2/sync/", {"station_protocol": protocol}, format="json")
        assert sync.status_code == 200, sync.data
        command = next(cmd for cmd in sync.json()["commands"] if cmd.get("order_id") == order_id)
        assert command["kind"] == "apply_order_manifest"
        assert command["task"]["task_type"] == (4 if placement == "advertising" else expected_type)
        if placement == "advertising":
            assert command["task"]["parameters"]["broadcast_type"] == expected_type
            assert command["task"]["parameters"]["order_parameters"]["suppress_background_audio"] is payload["suppress_background_audio"]
            assert command["task"]["parameters"]["order_parameters"]["suppress_background_visual"] is True
            assert command["task"]["parameters"]["order_parameters"]["audio_muted"] is params.get("audio_muted", False)
        assert {file["id"] for file in command["files"]} == set(bodies)
        assert all(file["name"] and file["sha256"] == hashlib.sha256(bodies[file["id"]].encode()).hexdigest()
                   for file in command["files"])
        cancelled = operator.post(f"/api/broadcast-orders/{order_id}/cancel/", format="json")
        assert cancelled.status_code == 200, cancelled.data
        sync = station.post("/api/station/v2/sync/", {"station_protocol": protocol}, format="json")
        cancellation = next(cmd for cmd in sync.json()["commands"] if cmd.get("order_id") == order_id)
        assert cancellation["kind"] == "cancel_order"
        assert cancellation["revision"] == command["revision"] + 1
        contracts.append({"policy": policy, "placement": placement, "expected_type": expected_type,
                          "apply": command, "cancel": cancellation, "bodies": bodies})
    output = os.environ.get("RMC_PLAYER_CONTRACT_OUTPUT")
    if output:
        Path(output).write_text(json.dumps(contracts, ensure_ascii=False, indent=2), encoding="utf-8")
