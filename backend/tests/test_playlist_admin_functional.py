"""Django admin keeps playlist graphs and Player delivery revisions in sync."""

from datetime import timedelta
from unittest.mock import PropertyMock

import pytest
from django.contrib.auth.models import Permission
from django.contrib.admin.models import DELETION, LogEntry
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from files.models import File, Playlist, PlaylistItem, PlaylistItemVisual
from files.playlist_admin_service import (
    snapshot_playlist_items,
    sync_playlist_graph,
)
from nomenclatures.models import StationCommandV2
from orders.models import Order


@pytest.fixture
def admin_media(super_user):
    specifications = [
        ("Audio A", 0, "audio-a.mp3"),
        ("Audio B", 0, "audio-b.mp3"),
        ("Image A", 2, "image-a.png"),
        ("Image B", 2, "image-b.png"),
    ]
    files = [
        File(
            name=name,
            type=media_type,
            source=source,
            owner=super_user,
            hash=str(index) * 96,
            md5hash=str(index) * 32,
            sha256hash=str(index) * 64,
            size=1,
        )
        for index, (name, media_type, source) in enumerate(specifications, 1)
    ]
    File.objects.bulk_create(files)
    return files


def _playlist_payload(playlist, rows, *, description="Admin edit"):
    payload = {
        "name": playlist.name,
        "description": description,
        "owner": str(playlist.owner_id or ""),
        "items-TOTAL_FORMS": str(len(rows)),
        "items-INITIAL_FORMS": str(sum(item is not None for item, *_ in rows)),
        "items-MIN_NUM_FORMS": "0",
        "items-MAX_NUM_FORMS": "1000",
        "_save": "Сохранить",
    }
    for index, (item, position, file, images) in enumerate(rows):
        payload[f"items-{index}-id"] = str(item.pk) if item is not None else ""
        payload[f"items-{index}-playlist"] = str(playlist.pk)
        payload[f"items-{index}-position"] = str(position)
        payload[f"items-{index}-file"] = str(file.pk)
        payload[f"items-{index}-images"] = [str(image.pk) for image in images]
    return payload


def _order(playlist, nomenclature, owner, name):
    return Order.objects.create(
        name=name,
        owner=owner,
        nomenclature=nomenclature,
        playlist=playlist,
        placement="advertising",
        parameters={"times_in_hour": 1},
        starts_at=timezone.now(),
        ends_at=timezone.now() + timedelta(days=1),
    )


@pytest.mark.django_db
def test_parent_admin_post_refreshes_all_orders_once_and_metadata_is_noop(
    client, super_user, admin_media, nomenclature, monkeypatch
):
    audio_a, audio_b, image_a, image_b = admin_media
    playlist = Playlist.objects.create(name="Admin graph", owner=super_user)
    first = PlaylistItem.objects.create(playlist=playlist, file=audio_a, position=0)
    second = PlaylistItem.objects.create(playlist=playlist, file=audio_b, position=1)
    original_visuals = [
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
    nomenclature.runtime_state = {
        "station_protocol": {
            "unified_orders_version": 1,
            "advertising_options_version": 1,
        }
    }
    nomenclature.save(update_fields=("runtime_state",))
    orders = [
        _order(playlist, nomenclature, super_user, "Order one"),
        _order(playlist, nomenclature, super_user, "Order two"),
    ]
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.test/file"))
    client.force_login(super_user)
    url = reverse("admin:files_playlist_change", args=(playlist.pk,))

    unchanged = _playlist_payload(
        playlist,
        [(first, 10, audio_a, [image_a, image_b]), (second, 20, audio_b, [])],
        description="Only metadata changed",
    )
    response = client.post(url, unchanged)
    assert response.status_code == 302
    assert list(playlist.items.order_by("position").values_list("position", flat=True)) == [10, 20]
    assert list(first.visuals.values_list("pk", "duration_seconds")) == [
        (row.pk, duration)
        for row, duration in zip(original_visuals, (7, 8, 9))
    ]
    assert not StationCommandV2.objects.exists()
    assert list(Order.objects.filter(pk__in=[order.pk for order in orders]).values_list("revision", flat=True)) == [1, 1]

    changed = _playlist_payload(
        playlist,
        [(second, 0, audio_b, []), (first, 1, audio_a, [image_b])],
    )
    response = client.post(url, changed)
    assert response.status_code == 302
    assert list(playlist.items.order_by("position").values_list("file_id", flat=True)) == [audio_b.pk, audio_a.pk]
    assert list(
        first.visuals.order_by("position").values_list(
            "file_id", "duration_seconds"
        )
    ) == [(image_b.pk, 7), (image_b.pk, 9)]
    assert list(Order.objects.filter(pk__in=[order.pk for order in orders]).values_list("revision", flat=True)) == [2, 2]
    assert StationCommandV2.objects.count() == 2


@pytest.mark.django_db
def test_parent_admin_legacy_guard_is_a_form_error_without_partial_write(
    client, super_user, admin_media, adorder
):
    audio_a, audio_b, image_a, image_b = admin_media
    playlist = Playlist.objects.create(name="Legacy admin", owner=super_user)
    playlist.files.add(audio_a)
    adorder.playlist = playlist
    adorder.save(update_fields=("playlist",))
    client.force_login(super_user)
    payload = _playlist_payload(playlist, [], description="Must roll back")
    payload["files_to_add"] = [str(audio_b.pk)]

    response = client.post(
        reverse("admin:files_playlist_change", args=(playlist.pk,)),
        payload,
    )

    assert response.status_code == 200
    assert "Сначала отмените активные заказы" in response.content.decode("utf-8")
    assert not playlist.items.exists()
    assert set(playlist.files.values_list("pk", flat=True)) == {audio_a.pk}


@pytest.mark.django_db
def test_adding_to_legacy_playlist_preserves_player_order_then_appends(
    client, super_user, admin_media
):
    audio_a, audio_b, image_a, image_b = admin_media
    by_uuid = sorted((audio_a, audio_b), key=lambda file: file.pk)
    File.objects.filter(pk=by_uuid[0].pk).update(
        created=timezone.now() - timedelta(days=2)
    )
    File.objects.filter(pk=by_uuid[1].pk).update(
        created=timezone.now() - timedelta(days=1)
    )
    playlist = Playlist.objects.create(name="Legacy order", owner=super_user)
    playlist.files.set(by_uuid)
    expected_old_order = [by_uuid[1].pk, by_uuid[0].pk]
    assert list(playlist.files.values_list("pk", flat=True)) == expected_old_order
    client.force_login(super_user)
    payload = _playlist_payload(playlist, [])
    payload["files_to_add"] = [str(image_a.pk)]

    response = client.post(
        reverse("admin:files_playlist_change", args=(playlist.pk,)),
        payload,
    )

    assert response.status_code == 302
    assert list(
        playlist.items.order_by("position").values_list("file_id", flat=True)
    ) == [*expected_old_order, image_a.pk]


@pytest.mark.django_db
def test_duplicate_action_clones_complete_graph_and_copy_is_independent(
    client, super_user, admin_media
):
    audio_a, audio_b, image_a, image_b = admin_media
    source = Playlist.objects.create(name="X" * 255, description="Source", owner=super_user)
    first = PlaylistItem.objects.create(playlist=source, file=audio_a, position=4, weight=65)
    second = PlaylistItem.objects.create(playlist=source, file=audio_b, position=9, weight=35)
    source_visuals = [
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
    source.files.set((audio_a, audio_b))
    client.force_login(super_user)

    response = client.post(
        reverse("admin:files_playlist_changelist"),
        {
            "action": "duplicate_playlist",
            "_selected_action": [str(source.pk)],
            "select_across": "0",
            "index": "0",
        },
    )

    assert response.status_code == 302
    copied = Playlist.objects.exclude(pk=source.pk).get()
    assert len(copied.name) <= 255
    assert copied.owner == super_user
    copied_items = list(copied.items.order_by("position"))
    assert [(item.position, item.file_id, item.weight) for item in copied_items] == [
        (4, audio_a.pk, 65),
        (9, audio_b.pk, 35),
    ]
    copied_visuals = list(copied_items[0].visuals.order_by("position"))
    assert [(row.file_id, row.duration_seconds) for row in copied_visuals] == [
        (image_b.pk, 7),
        (image_a.pk, 8),
        (image_b.pk, 9),
    ]
    assert {row.pk for row in copied_visuals}.isdisjoint(row.pk for row in source_visuals)
    copied_items[0].visuals.first().delete()
    assert first.visuals.count() == 3
    assert not copied.broadcast_orders.exists()
    assert not source.broadcast_orders.exists()
    assert not StationCommandV2.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_parent_admin_rolls_back_graph_and_all_orders_when_second_enqueue_fails(
    client, super_user, admin_media, nomenclature, monkeypatch
):
    audio_a, audio_b, image_a, image_b = admin_media
    playlist = Playlist.objects.create(name="Rollback graph", owner=super_user)
    item = PlaylistItem.objects.create(playlist=playlist, file=audio_a, position=7)
    PlaylistItemVisual.objects.create(playlist_item=item, file=image_a, position=3)
    playlist.files.add(audio_a)
    nomenclature.runtime_state = {
        "station_protocol": {
            "unified_orders_version": 1,
            "advertising_options_version": 1,
        }
    }
    nomenclature.save(update_fields=("runtime_state",))
    orders = [
        _order(playlist, nomenclature, super_user, "Rollback one"),
        _order(playlist, nomenclature, super_user, "Rollback two"),
    ]
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.test/file"))
    from orders.services.unified_order_delivery import enqueue_order

    calls = []

    def fail_second(order):
        command = enqueue_order(order)
        calls.append(order.pk)
        if len(calls) == 2:
            raise RuntimeError("second enqueue failed")
        return command

    monkeypatch.setattr(
        "orders.services.unified_order_delivery.enqueue_order",
        fail_second,
    )
    client.force_login(super_user)
    payload = _playlist_payload(
        playlist,
        [(item, 7, audio_a, [image_a, image_b])],
    )

    response = client.post(
        reverse("admin:files_playlist_change", args=(playlist.pk,)),
        payload,
    )

    assert response.status_code == 302
    assert any(
        "Не удалось обновить доставку Player" in str(message)
        for message in get_messages(response.wsgi_request)
    )
    assert list(item.visuals.values_list("file_id", flat=True)) == [image_a.pk]
    assert list(
        Order.objects.filter(pk__in=[order.pk for order in orders]).values_list(
            "revision", flat=True
        )
    ) == [1, 1]
    assert not StationCommandV2.objects.exists()


@pytest.mark.django_db
def test_reorder_alone_refreshes_once_then_identical_graph_is_noop(
    super_user, admin_media, nomenclature, monkeypatch
):
    audio_a, audio_b, image_a, image_b = admin_media
    playlist = Playlist.objects.create(name="Reorder only", owner=super_user)
    PlaylistItem.objects.create(playlist=playlist, file=audio_a, position=5)
    PlaylistItem.objects.create(playlist=playlist, file=audio_b, position=15)
    playlist.files.set((audio_a, audio_b))
    nomenclature.runtime_state = {
        "station_protocol": {
            "unified_orders_version": 1,
            "advertising_options_version": 1,
        }
    }
    nomenclature.save(update_fields=("runtime_state",))
    order = _order(playlist, nomenclature, super_user, "Reorder delivery")
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.test/file"))
    desired = list(reversed(snapshot_playlist_items(playlist)))
    desired[0]["position"], desired[1]["position"] = 5, 15

    assert sync_playlist_graph(playlist, desired) is True
    order.refresh_from_db()
    assert order.revision == 2
    assert StationCommandV2.objects.count() == 1

    assert sync_playlist_graph(playlist, snapshot_playlist_items(playlist)) is False
    order.refresh_from_db()
    assert order.revision == 2
    assert StationCommandV2.objects.count() == 1




@pytest.mark.django_db
def test_duplicate_action_requires_add_permission(
    client, django_user_model, super_user, admin_media
):
    source = Playlist.objects.create(name="Permission source", owner=super_user)
    staff = django_user_model.objects.create_user(
        email="playlist-editor@test.com",
        phone_number="+78005550101",
        password="test",
        role="ordinary",
        is_staff=True,
    )
    staff.user_permissions.add(
        Permission.objects.get(codename="view_playlist"),
        Permission.objects.get(codename="change_playlist"),
    )
    client.force_login(staff)

    response = client.post(
        reverse("admin:files_playlist_changelist"),
        {"action": "duplicate_playlist", "_selected_action": [str(source.pk)]},
    )

    assert response.status_code == 302
    assert Playlist.objects.count() == 1


@pytest.mark.django_db
def test_standalone_item_move_syncs_source_target_and_delivery(
    client, super_user, admin_media, nomenclature, monkeypatch
):
    audio_a, audio_b, image_a, image_b = admin_media
    source = Playlist.objects.create(name="Move source", owner=super_user)
    moving = PlaylistItem.objects.create(playlist=source, file=audio_a, position=5)
    retained = PlaylistItem.objects.create(playlist=source, file=audio_b, position=15)
    source.files.set((audio_a, audio_b))
    target = Playlist.objects.create(name="Move target", owner=super_user)
    target_item = PlaylistItem.objects.create(playlist=target, file=image_a, position=8)
    target.files.add(image_a)
    nomenclature.runtime_state = {
        "station_protocol": {
            "unified_orders_version": 1,
            "advertising_options_version": 1,
        }
    }
    nomenclature.save(update_fields=("runtime_state",))
    orders = [
        _order(source, nomenclature, super_user, "Source order"),
        _order(target, nomenclature, super_user, "Target order"),
    ]
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.test/file"))
    client.force_login(super_user)

    response = client.post(
        reverse("admin:files_playlistitem_change", args=(moving.pk,)),
        {
            "playlist": str(target.pk),
            "file": str(audio_a.pk),
            "position": "50",
            "visuals-TOTAL_FORMS": "0",
            "visuals-INITIAL_FORMS": "0",
            "visuals-MIN_NUM_FORMS": "0",
            "visuals-MAX_NUM_FORMS": "1000",
            "_save": "Сохранить",
        },
    )

    assert response.status_code == 302
    moving.refresh_from_db()
    assert moving.playlist_id == target.pk
    assert moving.position == 50
    assert list(source.items.values_list("file_id", flat=True)) == [retained.file_id]
    assert set(source.files.values_list("pk", flat=True)) == {audio_b.pk}
    assert set(target.files.values_list("pk", flat=True)) == {image_a.pk, audio_a.pk}
    assert list(
        Order.objects.filter(pk__in=[order.pk for order in orders]).values_list(
            "revision", flat=True
        )
    ) == [2, 2]
    assert StationCommandV2.objects.count() == 2


@pytest.mark.django_db
def test_clear_action_is_all_or_nothing_when_one_playlist_is_in_use(
    client, super_user, admin_media, nomenclature
):
    audio_a, audio_b, image_a, image_b = admin_media
    free = Playlist.objects.create(name="Free clear", owner=super_user)
    free_item = PlaylistItem.objects.create(playlist=free, file=audio_a, position=2)
    free.files.add(audio_a)
    busy = Playlist.objects.create(name="Busy clear", owner=super_user)
    busy_item = PlaylistItem.objects.create(playlist=busy, file=audio_b, position=4)
    busy.files.add(audio_b)
    _order(busy, nomenclature, super_user, "Busy order")
    client.force_login(super_user)

    response = client.post(
        reverse("admin:files_playlist_changelist"),
        {
            "action": "clear_playlist",
            "_selected_action": [str(free.pk), str(busy.pk)],
        },
    )

    assert response.status_code == 302
    assert PlaylistItem.objects.filter(pk__in=(free_item.pk, busy_item.pk)).count() == 2
    assert set(free.files.values_list("pk", flat=True)) == {audio_a.pk}
    assert set(busy.files.values_list("pk", flat=True)) == {audio_b.pk}


@pytest.mark.django_db
def test_standalone_delete_refreshes_once_and_last_active_item_is_blocked(
    client, super_user, admin_media, nomenclature, monkeypatch
):
    audio_a, audio_b, image_a, image_b = admin_media
    playlist = Playlist.objects.create(name="Delete items", owner=super_user)
    first = PlaylistItem.objects.create(playlist=playlist, file=audio_a, position=3)
    last = PlaylistItem.objects.create(playlist=playlist, file=audio_b, position=9)
    playlist.files.set((audio_a, audio_b))
    nomenclature.runtime_state = {
        "station_protocol": {
            "unified_orders_version": 1,
            "advertising_options_version": 1,
        }
    }
    nomenclature.save(update_fields=("runtime_state",))
    order = _order(playlist, nomenclature, super_user, "Delete order")
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.test/file"))
    client.force_login(super_user)

    response = client.post(
        reverse("admin:files_playlistitem_delete", args=(first.pk,)),
        {"post": "yes"},
    )
    assert response.status_code == 302
    assert not PlaylistItem.objects.filter(pk=first.pk).exists()
    assert LogEntry.objects.filter(
        object_id=str(first.pk),
        action_flag=DELETION,
    ).exists()
    order.refresh_from_db()
    assert order.revision == 2
    assert StationCommandV2.objects.count() == 1

    response = client.post(
        reverse("admin:files_playlistitem_delete", args=(last.pk,)),
        {"post": "yes"},
    )
    assert response.status_code == 200
    assert PlaylistItem.objects.filter(pk=last.pk).exists()
    order.refresh_from_db()
    assert order.revision == 2
    assert StationCommandV2.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_standalone_delete_delivery_failure_rolls_back_data_and_audit_log(
    client, super_user, admin_media, nomenclature, monkeypatch
):
    audio_a, audio_b, image_a, image_b = admin_media
    playlist = Playlist.objects.create(name="Delete rollback", owner=super_user)
    deleting = PlaylistItem.objects.create(playlist=playlist, file=audio_a, position=2)
    PlaylistItem.objects.create(playlist=playlist, file=audio_b, position=7)
    playlist.files.set((audio_a, audio_b))
    nomenclature.runtime_state = {
        "station_protocol": {
            "unified_orders_version": 1,
            "advertising_options_version": 1,
        }
    }
    nomenclature.save(update_fields=("runtime_state",))
    orders = [
        _order(playlist, nomenclature, super_user, "Delete rollback one"),
        _order(playlist, nomenclature, super_user, "Delete rollback two"),
    ]
    monkeypatch.setattr(File, "url", PropertyMock(return_value="https://media.test/file"))
    from orders.services.unified_order_delivery import enqueue_order

    calls = []

    def fail_second(order):
        command = enqueue_order(order)
        calls.append(order.pk)
        if len(calls) == 2:
            raise RuntimeError("delete delivery failed")
        return command

    monkeypatch.setattr(
        "orders.services.unified_order_delivery.enqueue_order",
        fail_second,
    )
    client.force_login(super_user)

    response = client.post(
        reverse("admin:files_playlistitem_delete", args=(deleting.pk,)),
        {"post": "yes"},
    )

    assert response.status_code == 302
    assert PlaylistItem.objects.filter(pk=deleting.pk).exists()
    assert not LogEntry.objects.filter(
        object_id=str(deleting.pk),
        action_flag=DELETION,
    ).exists()
    assert list(
        Order.objects.filter(pk__in=[order.pk for order in orders]).values_list(
            "revision", flat=True
        )
    ) == [1, 1]
    assert not StationCommandV2.objects.exists()
