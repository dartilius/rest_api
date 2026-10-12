"""Playlist editor binds visuals to their audio without turning them into ads."""

from types import SimpleNamespace

import pytest
from django.contrib.admin.sites import site
from django.forms import inlineformset_factory
from django.urls import reverse

from files.models import File, Playlist, PlaylistItem, PlaylistItemVisual
from files.playlist_admin_forms import PlaylistItemInlineForm
from orders.services.unified_order_delivery import _playlist_payload


@pytest.fixture
def media(super_user):
    files = [File(name=name, type=kind, source=source, owner=super_user, hash=str(i) * 96,
                  md5hash=str(i) * 32, sha256hash=str(i) * 64, size=1)
        for i, (name, kind, source) in enumerate([
            ("Audio A", 0, "a.mp3"), ("Audio B", 0, "b.mp3"),
            ("Picture A", 2, "a.png"), ("Picture B", 2, "b.png"), ("Video", 1, "v.mp4")], 1)]
    File.objects.bulk_create(files)
    return files


@pytest.mark.django_db
def test_new_playlist_saves_audio_and_its_images_in_one_formset(media, super_user, rf):
    audio, other_audio, first, second, video = media
    playlist = Playlist(name="New playlist", owner=super_user)
    Factory = inlineformset_factory(Playlist, PlaylistItem, form=PlaylistItemInlineForm,
        fields=("position", "file", "images"), extra=0)
    data = {"items-TOTAL_FORMS": "2", "items-INITIAL_FORMS": "0",
        "items-0-position": "0", "items-0-file": str(audio.pk), "items-0-images": [str(second.pk), str(first.pk)],
        "items-1-position": "1", "items-1-file": str(other_audio.pk), "items-1-images": []}
    formset = Factory(instance=playlist, data=data, prefix="items")
    assert formset.is_valid(), formset.errors
    playlist.save()
    request = rf.post("/admin/files/playlist/add/")
    request.user = super_user
    site._registry[Playlist].save_formset(request, SimpleNamespace(instance=playlist), formset, change=False)
    items = list(playlist.items.order_by("position"))
    assert list(items[0].visuals.values_list("file_id", flat=True)) == [second.pk, first.pk]
    assert not items[1].visuals.exists()
    assert set(playlist.files.values_list("pk", flat=True)) == {audio.pk, other_audio.pk}
    primary, slides, all_files = _playlist_payload(SimpleNamespace(playlist=playlist, placement="advertising"))
    assert slides == {str(audio.pk): [str(second.pk), str(first.pk)]}
    assert {item["id"] for item in primary} == {str(audio.pk), str(other_audio.pk)}
    assert len(all_files) == 4
    assert _playlist_payload(SimpleNamespace(playlist=playlist, placement="background"))[1] == {}


@pytest.mark.django_db
def test_edit_retains_visual_rows_order_duplicates_and_duration(media):
    audio, other_audio, first, second, video = media
    playlist = Playlist.objects.create(name="Existing")
    item = PlaylistItem.objects.create(playlist=playlist, file=audio, position=0)
    rows = [PlaylistItemVisual.objects.create(playlist_item=item, file=file, position=i, duration_seconds=9)
        for i, file in enumerate([second, first, second])]
    form = PlaylistItemInlineForm(instance=item, data={"position": 0, "file": str(audio.pk), "images": [str(first.pk), str(second.pk)]})
    assert form.is_valid(), form.errors
    form.save()
    form.save_images()
    assert list(item.visuals.values_list("pk", flat=True)) == [row.pk for row in rows]
    assert list(item.visuals.values_list("duration_seconds", flat=True)) == [9, 9, 9]
    item = PlaylistItem.objects.prefetch_related("visuals").get(pk=item.pk)
    form = PlaylistItemInlineForm(instance=item, data={"position": 0, "file": str(audio.pk), "images": [str(second.pk)]})
    assert form.is_valid(), form.errors
    form.save_images()
    assert list(item.visuals.values_list("file_id", flat=True)) == [second.pk, second.pk]
    assert File.objects.filter(pk=first.pk).exists()


@pytest.mark.django_db
def test_non_audio_cannot_receive_new_images_and_page_has_same_editor(client, media, super_user):
    audio, other_audio, first, second, video = media
    form = PlaylistItemInlineForm(data={"position": 0, "file": str(video.pk), "images": [str(first.pk)]})
    assert not form.is_valid() and "images" in form.errors
    client.force_login(super_user)
    response = client.get(reverse("admin:files_playlist_add"))
    assert response.status_code == 200
    assert "Картинки к этому аудио" in response.content.decode()


@pytest.mark.django_db
def test_image_autocomplete_only_returns_active_images(media, super_user, rf):
    request = rf.get("/admin/autocomplete/", {"app_label": "files", "model_name": "playlistitemvisual", "field_name": "file"})
    request.user = super_user
    result, _ = site._registry[File].get_search_results(request, File.objects.all(), "")
    assert set(result.values_list("pk", flat=True)) == {media[2].pk, media[3].pk}


@pytest.mark.django_db
def test_existing_inactive_image_is_preserved_but_new_inactive_image_is_rejected(media):
    audio, other_audio, first, second, video = media
    File.objects.filter(pk__in=[first.pk, second.pk]).update(is_active=False)
    playlist = Playlist.objects.create(name="Legacy pictures")
    item = PlaylistItem.objects.create(playlist=playlist, file=audio, position=0)
    link = PlaylistItemVisual.objects.create(playlist_item=item, file=first, position=0)
    form = PlaylistItemInlineForm(instance=item, data={"position": 0, "file": str(audio.pk), "images": [str(first.pk)]})
    assert form.is_valid(), form.errors
    form.save_images()
    assert item.visuals.get().pk == link.pk
    form = PlaylistItemInlineForm(instance=item, data={"position": 0, "file": str(audio.pk), "images": [str(second.pk)]})
    assert not form.is_valid() and "images" in form.errors
