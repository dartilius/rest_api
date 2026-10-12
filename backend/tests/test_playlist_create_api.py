"""Existing POST playlists accepts ordered content without breaking legacy files."""

from unittest.mock import PropertyMock
from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from files.models import File, Playlist, PlaylistItem, PlaylistItemVisual
from orders.services.unified_order_delivery import _playlist_payload
from types import SimpleNamespace


@pytest.fixture
def api_media(super_user, monkeypatch):
    files = [File(name=name, type=kind, source=source, owner=super_user, hash=str(i) * 96,
        md5hash=str(i) * 32, sha256hash=str(i) * 64, size=1)
        for i, (name, kind, source) in enumerate([
            ("Audio A", 0, "a.mp3"), ("Audio B", 0, "b.mp3"),
            ("Image A", 2, "a.png"), ("Image B", 2, "b.png"), ("Video", 1, "v.mp4")], 1)]
    File.objects.bulk_create(files)
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.example.test/clip"))
    client = APIClient()
    client.force_authenticate(super_user)
    return client, files


@pytest.mark.django_db
def test_structured_create_and_retrieve_keep_audio_images_and_order(api_media):
    client, media = api_media
    audio, other, first, second, video = media
    response = client.post("/api/playlists/", {"name": "Structured", "items": [
        {"file": str(audio.pk), "images": [str(second.pk), str(first.pk)]},
        {"file": str(other.pk), "images": []}, {"file": str(video.pk)},
    ]}, format="json")
    assert response.status_code == 201, response.data
    playlist = Playlist.objects.get(pk=response.data["id"])
    assert set(playlist.files.values_list("pk", flat=True)) == {audio.pk, other.pk, video.pk}
    fetched = client.get(f"/api/playlists/{playlist.pk}/")
    assert fetched.status_code == 200
    assert fetched.data["items"][0]["images"] == [str(second.pk), str(first.pk)]
    assert fetched.data["items"][1]["images"] == []
    assert fetched.data["items"][0]["image_files"][0]["name"] == second.name
    assert _playlist_payload(SimpleNamespace(playlist=playlist, placement="advertising"))[1] == {
        str(audio.pk): [str(second.pk), str(first.pk)]}


@pytest.mark.django_db
def test_legacy_files_format_keeps_response_and_metadata_patch(api_media):
    client, media = api_media
    response = client.post("/api/playlists/", {"name": "Legacy", "files": [str(media[0].pk), str(media[1].pk)]}, format="json")
    assert response.status_code == 201, response.data
    assert len(response.data["files"]) == 2 and response.data["items"] == []
    assert not PlaylistItem.objects.exists()
    result = client.patch(f"/api/playlists/{response.data['id']}/", {"description": "Updated"}, format="json")
    assert result.status_code == 200, result.data
    mixed = client.post("/api/playlists/", {"name": "Bad mixed legacy", "files": [str(media[0].pk), str(media[4].pk)]}, format="json")
    assert mixed.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["both", "missing", "empty", "unknown", "inactive", "nonimage", "nonaudio", "duplicate"])
def test_bad_composition_creates_no_parent_or_links(api_media, case):
    client, media = api_media
    payload = {"name": "Invalid", "items": [{"file": str(media[0].pk), "images": [str(media[2].pk)]}]}
    if case == "both": payload["files"] = [str(media[0].pk)]
    elif case == "missing": payload.pop("items")
    elif case == "empty": payload["items"] = []
    elif case == "unknown": payload["items"][0]["images"] = [str(uuid4())]
    elif case == "inactive": File.objects.filter(pk=media[2].pk).update(is_active=False)
    elif case == "nonimage": payload["items"][0]["images"] = [str(media[1].pk)]
    elif case == "nonaudio": payload["items"][0]["file"] = str(media[4].pk)
    else: payload["items"].append(payload["items"][0])
    response = client.post("/api/playlists/", payload, format="json")
    assert response.status_code == 400, response.data
    assert not Playlist.objects.exists() and not PlaylistItemVisual.objects.exists()


@pytest.mark.django_db
def test_bulk_creation_rolls_back_all_graphs_on_second_write_failure(api_media, monkeypatch):
    import files.serializers as serializers
    client, media = api_media
    original = serializers.create_playlist_items
    calls = []
    def fail_second(playlist, items):
        original(playlist, items)
        calls.append(playlist.pk)
        if len(calls) == 2:
            raise RuntimeError("Test graph failure")
    monkeypatch.setattr(serializers, "create_playlist_items", fail_second)
    payload = [{"name": name, "items": [{"file": str(media[0].pk), "images": [str(media[2].pk)]}]} for name in ("One", "Two")]
    with pytest.raises(RuntimeError, match="Test graph failure"):
        client.post("/api/playlists/", payload, format="json")
    assert not Playlist.objects.exists() and not PlaylistItem.objects.exists() and not PlaylistItemVisual.objects.exists()
