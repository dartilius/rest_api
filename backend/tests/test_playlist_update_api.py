"""REST composition changes, delivery and rollback contracts."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from files.models import File, PlaylistItem, PlaylistItemVisual
from nomenclatures.models import StationCommandV2
from orders.models import BgOrder, Order
from tests.test_playlist_mutations import mutation_media, structured_playlist


@pytest.fixture
def editor(super_user, structured_playlist):
    client = APIClient()
    client.force_authenticate(super_user)
    return client


@pytest.fixture
def active_order(structured_playlist, nomenclature, user, monkeypatch):
    from unittest.mock import PropertyMock

    playlist, *_ = structured_playlist
    nomenclature.runtime_state = {"station_protocol": {"unified_orders_version": 1}}
    nomenclature.save(update_fields=["runtime_state"])
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.test/file"))
    return Order.objects.create(name="Active", owner=user, nomenclature=nomenclature,
        playlist=playlist, placement="advertising", playback_policy="workday",
        suppress_background_audio=True, suppress_background_visual=True,
        parameters={"times_in_hour": 1}, starts_at=timezone.now(),
        ends_at=timezone.now() + timedelta(days=1))


@pytest.mark.django_db
def test_patch_reorders_and_delivers_new_revision(editor, structured_playlist, mutation_media, active_order):
    playlist, first, second, visuals = structured_playlist
    a, b, _, image_a, image_b = mutation_media
    response = editor.patch(f"/api/playlists/{playlist.pk}/", {"items": [
        {"file": str(b.pk)}, {"file": str(a.pk), "images": [str(image_b.pk), str(image_a.pk)]}
    ]}, format="json")
    assert response.status_code == 200, response.data
    assert [row["file"] for row in response.data["items"]] == [str(b.pk), str(a.pk)]
    assert list(playlist.items.order_by("position").values_list("pk", flat=True)) == [second.pk, first.pk]
    assert list(first.visuals.order_by("position").values_list("pk", flat=True)) == [visuals[0].pk, visuals[1].pk]
    active_order.refresh_from_db()
    assert active_order.revision == 2
    command = StationCommandV2.objects.get()
    assert command.body["revision"] == 2
    assert command.body["order_id"] == str(active_order.pk)


@pytest.mark.django_db
def test_metadata_and_identical_snapshot_do_not_redeliver(editor, structured_playlist, active_order):
    playlist, *_ = structured_playlist
    snapshot = [{"file": str(item.file_id), "images": [str(v.file_id) for v in item.visuals.order_by("position")]}
        for item in playlist.items.order_by("position")]
    for payload in ({"description": "Edited"}, {"items": snapshot}):
        response = editor.patch(f"/api/playlists/{playlist.pk}/", payload, format="json")
        assert response.status_code == 200, response.data
    active_order.refresh_from_db()
    assert active_order.revision == 1
    assert not StationCommandV2.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["files", "add_files", "remove_files"])
def test_primary_changes_preserve_retained_audio_visuals(editor, structured_playlist, mutation_media, active_order, operation):
    playlist, first, _, visuals = structured_playlist
    a, b, c, *_ = mutation_media
    if operation == "files":
        response = editor.patch(f"/api/playlists/{playlist.pk}/", {"files": [str(a.pk), str(c.pk)]}, format="json")
        expected = [a.pk, c.pk]
    else:
        identity = c.pk if operation == "add_files" else b.pk
        response = editor.post(f"/api/playlists/{playlist.pk}/{operation}/", {"files": [str(identity)]}, format="json")
        expected = [a.pk, b.pk, c.pk] if operation == "add_files" else [a.pk]
    assert response.status_code == 200, response.data
    assert list(playlist.items.order_by("position").values_list("file_id", flat=True)) == expected
    assert list(first.visuals.order_by("position").values_list("pk", flat=True)) == [v.pk for v in visuals]
    active_order.refresh_from_db()
    assert active_order.revision == 2
    assert StationCommandV2.objects.count() == 1


@pytest.mark.django_db
def test_enqueue_failure_rolls_back_metadata_graph_and_revision(editor, structured_playlist, mutation_media, active_order, monkeypatch):
    playlist, first, second, visuals = structured_playlist
    original_name = playlist.name

    def fail(_playlist):
        raise RuntimeError("delivery failure")

    monkeypatch.setattr("files.serializers.refresh_playlist_orders", fail)
    with pytest.raises(RuntimeError, match="delivery failure"):
        editor.patch(f"/api/playlists/{playlist.pk}/", {"name": "Changed", "items": [
            {"file": str(mutation_media[2].pk)}]}, format="json")
    playlist.refresh_from_db()
    assert playlist.name == original_name
    assert list(playlist.items.order_by("position").values_list("pk", flat=True)) == [first.pk, second.pk]
    assert PlaylistItemVisual.objects.filter(pk__in=[v.pk for v in visuals]).count() == 3
    active_order.refresh_from_db()
    assert active_order.revision == 1
    assert not StationCommandV2.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("payload_kind", ["empty", "unknown", "both", "nonimage", "extra", "missing_file"])
def test_invalid_patch_does_not_change_graph(editor, structured_playlist, mutation_media, active_order, payload_kind):
    playlist, first, second, *_ = structured_playlist
    payload = {"items": [{"file": str(mutation_media[0].pk)}]}
    if payload_kind == "empty": payload = {"items": []}
    elif payload_kind == "unknown": payload["items"][0]["file"] = str(uuid4())
    elif payload_kind == "both": payload["files"] = [str(mutation_media[0].pk)]
    elif payload_kind == "nonimage": payload["items"][0]["images"] = [str(mutation_media[1].pk)]
    elif payload_kind == "missing_file": payload["items"] = [{}]
    else: payload["unexpected"] = True
    response = editor.patch(f"/api/playlists/{playlist.pk}/", payload, format="json")
    assert response.status_code == 400, response.data
    assert list(playlist.items.order_by("position").values_list("pk", flat=True)) == [first.pk, second.pk]
    assert not StationCommandV2.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["items", "files"])
def test_full_replacement_rejected_for_active_legacy_order(editor, structured_playlist, mutation_media, nomenclature, user, field):
    playlist, first, second, *_ = structured_playlist
    BgOrder.objects.create(name="Legacy", owner=user, client=nomenclature, playlist=playlist,
        broadcast_interval=(timezone.now(), timezone.now() + timedelta(days=1)), order_type=0, parameters={})
    payload = {field: [{"file": str(mutation_media[2].pk)}] if field == "items" else [str(mutation_media[2].pk)]}
    response = editor.patch(f"/api/playlists/{playlist.pk}/", payload, format="json")
    assert response.status_code == 400, response.data
    assert list(playlist.items.order_by("position").values_list("pk", flat=True)) == [first.pk, second.pk]


@pytest.mark.django_db
def test_reorder_positions_near_int32_limit(editor, structured_playlist, mutation_media):
    playlist, first, second, visuals = structured_playlist
    PlaylistItem.objects.filter(pk=first.pk).update(position=2147483647)
    PlaylistItemVisual.objects.filter(pk=visuals[0].pk).update(position=2147483647)
    response = editor.patch(f"/api/playlists/{playlist.pk}/", {"items": [
        {"file": str(mutation_media[0].pk), "images": [str(mutation_media[3].pk), str(mutation_media[4].pk)]},
        {"file": str(mutation_media[1].pk)}]}, format="json")
    assert response.status_code == 200, response.data
    assert list(playlist.items.order_by("position").values_list("position", flat=True)) == [0, 1]


@pytest.mark.django_db
def test_unknown_remove_is_noop(editor, structured_playlist, active_order):
    playlist, *_ = structured_playlist
    response = editor.post(f"/api/playlists/{playlist.pk}/remove_files/", {"files": [str(uuid4())]}, format="json")
    assert response.status_code == 200
    active_order.refresh_from_db()
    assert active_order.revision == 1
    assert not StationCommandV2.objects.exists()


@pytest.mark.django_db
def test_empty_snapshot_allowed_without_active_orders(editor, structured_playlist):
    playlist, *_ = structured_playlist
    response = editor.patch(f"/api/playlists/{playlist.pk}/", {"items": []}, format="json")
    assert response.status_code == 200, response.data
    assert response.data["items"] == [] and response.data["files"] == []
    assert not playlist.items.exists()


@pytest.mark.django_db
def test_inactive_image_can_be_retained_but_not_duplicated(editor, structured_playlist, mutation_media):
    playlist, first, *_ = structured_playlist
    File.objects.filter(pk=mutation_media[3].pk).update(is_active=False)
    snapshot = [{"file": str(item.file_id), "images": [str(v.file_id) for v in item.visuals.order_by("position")]}
        for item in playlist.items.order_by("position")]
    response = editor.patch(f"/api/playlists/{playlist.pk}/", {"items": snapshot}, format="json")
    assert response.status_code == 200, response.data
    snapshot[0]["images"].append(str(mutation_media[3].pk))
    response = editor.patch(f"/api/playlists/{playlist.pk}/", {"items": snapshot}, format="json")
    assert response.status_code == 400, response.data
    assert first.visuals.count() == 3


@pytest.mark.django_db
def test_nonstaff_cannot_edit_and_put_remains_unsupported(editor, structured_playlist, user):
    playlist, *_ = structured_playlist
    url = f"/api/playlists/{playlist.pk}/"
    assert editor.put(url, {"name": "Replacement"}, format="json").status_code == 405
    ordinary = APIClient()
    ordinary.force_authenticate(user)
    assert ordinary.patch(url, {"name": "Forbidden"}, format="json").status_code == 403
    playlist.refresh_from_db()
    assert playlist.name == "Structured mutations"


@pytest.mark.django_db
def test_playlist_used_by_unified_order_cannot_be_deleted(editor, structured_playlist, active_order):
    playlist, *_ = structured_playlist
    response = editor.delete(f"/api/playlists/{playlist.pk}/")
    assert response.status_code == 400, response.data
    assert playlist.items.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize("payload", [[], "text", 123])
@pytest.mark.parametrize("operation", ["patch", "add_files", "remove_files"])
def test_nonobject_json_returns_validation_error(editor, structured_playlist, payload, operation):
    playlist, *_ = structured_playlist
    url = f"/api/playlists/{playlist.pk}/"
    response = (editor.patch(url, payload, format="json") if operation == "patch"
        else editor.post(url + operation + "/", payload, format="json"))
    assert response.status_code == 400, response.data
    assert playlist.items.count() == 2
