"""Playlist composition updates preserve identity and delivery consistency."""

from datetime import timedelta
from unittest.mock import PropertyMock

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from files.models import File, Playlist, PlaylistItem, PlaylistItemVisual
from files.playlist_mutations import (
    ensure_structured_editable,
    refresh_playlist_orders,
    replace_playlist_items,
    set_playlist_files,
)
from nomenclatures.models import StationCommandV2
from orders.models import Order
from tasks.models import Task


@pytest.fixture
def mutation_media(user):
    specifications = [
        ("Audio A", 0, "audio-a.mp3"),
        ("Audio B", 0, "audio-b.mp3"),
        ("Audio C", 0, "audio-c.mp3"),
        ("Image A", 2, "image-a.png"),
        ("Image B", 2, "image-b.png"),
    ]
    files = [
        File(
            name=name,
            type=media_type,
            source=source,
            owner=user,
            hash=str(index) * 96,
            md5hash=str(index) * 32,
            sha256hash=str(index) * 64,
            size=1,
        )
        for index, (name, media_type, source) in enumerate(specifications, 1)
    ]
    File.objects.bulk_create(files)
    return files


@pytest.fixture
def structured_playlist(user, mutation_media):
    audio_a, audio_b, _, image_a, image_b = mutation_media
    playlist = Playlist.objects.create(name="Structured mutations", owner=user)
    first = PlaylistItem.objects.create(
        playlist=playlist, file=audio_a, position=0
    )
    second = PlaylistItem.objects.create(
        playlist=playlist, file=audio_b, position=1
    )
    visuals = [
        PlaylistItemVisual.objects.create(
            playlist_item=first,
            file=file,
            position=position,
            duration_seconds=duration,
        )
        for position, (file, duration) in enumerate(
            ((image_b, 7), (image_a, 8), (image_b, 9))
        )
    ]
    playlist.files.set((audio_a, audio_b))
    return playlist, first, second, visuals


@pytest.mark.django_db
def test_replace_reorders_rows_and_keeps_visual_occurrence_identity(
    structured_playlist, mutation_media
):
    playlist, first, second, visuals = structured_playlist
    audio_a, audio_b, _, image_a, image_b = mutation_media

    with transaction.atomic():
        replace_playlist_items(
            playlist,
            [
                {"file": audio_b, "images": []},
                {"file": audio_a, "images": [image_b, image_b, image_a]},
            ],
        )

    items = list(playlist.items.order_by("position"))
    assert [(item.pk, item.file_id) for item in items] == [
        (second.pk, audio_b.pk),
        (first.pk, audio_a.pk),
    ]
    reordered = list(items[1].visuals.order_by("position"))
    assert [row.pk for row in reordered] == [
        visuals[0].pk,
        visuals[2].pk,
        visuals[1].pk,
    ]
    assert [row.duration_seconds for row in reordered] == [7, 9, 8]
    assert set(playlist.files.values_list("pk", flat=True)) == {
        audio_a.pk,
        audio_b.pk,
    }


@pytest.mark.django_db
def test_set_files_adapts_structured_graph_but_keeps_legacy_playlist_legacy(
    structured_playlist, mutation_media, user
):
    playlist, first, removed, visuals = structured_playlist
    audio_a, _, audio_c, image_a, image_b = mutation_media

    with transaction.atomic():
        set_playlist_files(playlist, [audio_a, audio_c])

    items = list(playlist.items.order_by("position"))
    assert (items[0].pk, items[0].file_id) == (first.pk, audio_a.pk)
    assert items[1].file_id == audio_c.pk
    assert items[1].pk != removed.pk
    assert list(items[0].visuals.values_list("pk", flat=True)) == [
        visual.pk for visual in visuals
    ]
    assert set(playlist.files.values_list("pk", flat=True)) == {
        audio_a.pk,
        audio_c.pk,
    }
    assert File.objects.filter(pk__in=(image_a.pk, image_b.pk)).count() == 2

    legacy = Playlist.objects.create(name="Legacy mutations", owner=user)
    legacy.files.add(audio_a)
    with transaction.atomic():
        set_playlist_files(legacy, [audio_a, audio_c])
    assert not legacy.items.exists()
    assert set(legacy.files.values_list("pk", flat=True)) == {
        audio_a.pk,
        audio_c.pk,
    }


@pytest.mark.django_db
def test_active_orders_block_empty_and_legacy_structured_replacement(
    structured_playlist, mutation_media, nomenclature, user, adorder
):
    playlist, _, _, _ = structured_playlist
    Order.objects.create(
        name="Active unified order",
        owner=user,
        nomenclature=nomenclature,
        playlist=playlist,
        placement="advertising",
        parameters={"times_in_hour": 1},
    )

    with pytest.raises(ValidationError, match="Сначала отмените активные заказы"):
        with transaction.atomic():
            set_playlist_files(playlist, [])
    assert playlist.items.count() == 2

    with pytest.raises(ValidationError, match="Сначала отмените активные заказы"):
        ensure_structured_editable(adorder.playlist)


def _make_unified_orders(playlist, nomenclature, user):
    common = {
        "owner": user,
        "nomenclature": nomenclature,
        "playlist": playlist,
        "placement": "advertising",
        "parameters": {"times_in_hour": 1},
        "suppress_background_audio": True,
        "suppress_background_visual": True,
        "starts_at": timezone.now(),
        "ends_at": timezone.now() + timedelta(days=1),
    }
    return [
        Order.objects.create(name="Active one", **common),
        Order.objects.create(name="Active two", **common),
        Order.objects.create(name="Completed", status=2, **common),
        Order.objects.create(name="Cancelled", status=3, is_active=False, **common),
    ]


@pytest.mark.django_db
def test_refresh_increments_active_revisions_and_enqueues_complete_commands(
    structured_playlist, nomenclature, user, monkeypatch
):
    playlist, _, _, _ = structured_playlist
    nomenclature.runtime_state = {
        "station_protocol": {"unified_orders_version": 1}
    }
    nomenclature.save(update_fields=("runtime_state",))
    orders = _make_unified_orders(playlist, nomenclature, user)
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.test/file"))

    with transaction.atomic():
        commands = refresh_playlist_orders(playlist)

    for order in orders:
        order.refresh_from_db()
    assert [order.revision for order in orders] == [2, 2, 1, 1]
    assert len(commands) == 2
    assert {command.body["revision"] for command in commands} == {2}
    assert {command.body["order_id"] for command in commands} == {
        str(orders[0].pk),
        str(orders[1].pk),
    }
    assert StationCommandV2.objects.count() == 2
    assert not Task.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_refresh_failure_rolls_back_all_revisions_and_commands(
    structured_playlist, nomenclature, user, monkeypatch
):
    playlist, _, _, _ = structured_playlist
    nomenclature.runtime_state = {
        "station_protocol": {"unified_orders_version": 1}
    }
    nomenclature.save(update_fields=("runtime_state",))
    orders = _make_unified_orders(playlist, nomenclature, user)[:2]
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.test/file"))
    from orders.services.unified_order_delivery import enqueue_order

    calls = []

    def fail_after_second(order):
        command = enqueue_order(order)
        calls.append(order.pk)
        if len(calls) == 2:
            raise RuntimeError("second delivery failed")
        return command

    monkeypatch.setattr(
        "orders.services.unified_order_delivery.enqueue_order", fail_after_second
    )

    with pytest.raises(RuntimeError, match="second delivery failed"):
        with transaction.atomic():
            refresh_playlist_orders(playlist)

    assert list(
        Order.objects.filter(pk__in=[order.pk for order in orders])
        .order_by("name")
        .values_list("revision", flat=True)
    ) == [1, 1]
    assert not StationCommandV2.objects.exists()
