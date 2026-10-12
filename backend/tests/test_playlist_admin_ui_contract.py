"""Functional playlist fixes retain the manager's existing controls."""

import pytest
from django.urls import reverse

from files.models import Playlist, PlaylistItem, PlaylistItemVisual
from tests.test_playlist_audio_images import media


@pytest.mark.django_db
def test_playlist_editor_retains_existing_fields_and_audio_image_selector(client, super_user, media):
    playlist = Playlist.objects.create(name="UI playlist", owner=super_user)
    audio, _, image, *_ = media
    item = PlaylistItem.objects.create(playlist=playlist, file=audio, position=0)
    PlaylistItemVisual.objects.create(playlist_item=item, file=image, position=0)
    playlist.files.add(audio)
    client.force_login(super_user)
    response = client.get(reverse("admin:files_playlist_change", args=[playlist.pk]))
    assert response.status_code == 200
    parent = response.context["adminform"].form
    assert {"name", "description", "owner", "files_to_add"} <= parent.fields.keys()
    html = response.content.decode("utf-8")
    assert 'name="items-0-file"' in html
    assert 'name="items-0-position"' in html
    assert 'name="items-0-images"' in html
    assert "Картинки к этому аудио" in html


@pytest.mark.django_db
def test_standalone_item_editor_keeps_playlist_editable(client, super_user, media):
    playlist = Playlist.objects.create(name="UI standalone item", owner=super_user)
    item = PlaylistItem.objects.create(playlist=playlist, file=media[0], position=0)
    playlist.files.add(media[0])
    client.force_login(super_user)
    response = client.get(reverse("admin:files_playlistitem_change", args=[item.pk]))
    assert response.status_code == 200
    form = response.context["adminform"].form
    assert {"playlist", "position", "file"} <= form.fields.keys()
    assert form.fields["playlist"].disabled is False
    assert 'name="playlist"' in response.content.decode("utf-8")
