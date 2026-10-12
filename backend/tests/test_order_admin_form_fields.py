"""Managers configure orders through typed controls without JSON input."""

import pytest
from django.contrib.admin.sites import site
from django.urls import reverse

from files.models import File, Playlist
from orders.models import Order


@pytest.fixture
def manager_form(nomenclature, super_user, rf, monkeypatch):
    monkeypatch.setattr("orders.admin_forms.validate_order_delivery", lambda obj: None)
    playlist = Playlist.objects.create(name="Manager playlist")
    request = rf.get("/admin/orders/order/add/")
    request.user = super_user
    admin = site._registry[Order]
    data = {"name": "New campaign", "placement": "advertising", "playback_policy": "workday",
        "playlist": str(playlist.pk), "target_nomenclatures": [str(nomenclature.pk)],
        "starts_at_0": "2026-10-08", "starts_at_1": "09:00:00", "ends_at_0": "2026-10-09", "ends_at_1": "18:00:00",
        "times_in_hour": "4", "order_weight": "70", "advertising_audio": "sound",
        "suppress_background_audio": "on", "suppress_background_visual": "on"}
    return admin, request, data, nomenclature, playlist


@pytest.mark.django_db
@pytest.mark.parametrize("policy,extra,expected", [
    ("workday", {}, {"times_in_hour": 4}),
    ("open_offset", {"offset_minutes": "30", "offset_seconds": "0"}, {"times_in_hour": 4, "timedelta": "00:30:00"}),
    ("close_offset", {"offset_minutes": "5", "offset_seconds": "30"}, {"times_in_hour": 4, "timedelta": "00:05:30"}),
    ("fixed_time", {"start_time": "10:00", "end_time": "17:30"}, {"times_in_hour": 4, "start_time": "10:00:00", "end_time": "17:30:00"}),
    ("open_to_fixed", {"end_time": "17:30"}, {"times_in_hour": 4, "end_time": "17:30:00"}),
    ("fixed_to_close", {"start_time": "10:00"}, {"times_in_hour": 4, "start_time": "10:00:00"}),
    ("start_to_close", {"start_time": "10:07:30"}, {"times_in_hour": 4, "start_time": "10:07:30"}),
])
def test_schedule_controls_build_compatible_parameters(manager_form, policy, extra, expected):
    admin, request, data, point, playlist = manager_form
    form = admin.get_form(request)(data={**data, "playback_policy": policy, **extra})
    assert "parameters" not in form.fields
    assert form.is_valid(), form.errors
    for key, value in expected.items():
        assert form.instance.parameters[key] == value


@pytest.mark.django_db
@pytest.mark.parametrize("muted", [False, True])
def test_continuous_needs_no_frequency_and_normalizes_background(manager_form, muted):
    admin, request, data, point, playlist = manager_form
    data.pop("times_in_hour")
    form = admin.get_form(request)(data={**data, "playback_policy": "continuous", "advertising_audio": "muted" if muted else "sound"})
    assert form.is_valid(), form.errors
    assert form.instance.parameters["audio_muted"] is muted
    assert "times_in_hour" not in form.instance.parameters
    assert form.instance.suppress_background_audio is (not muted)
    assert form.instance.suppress_background_visual is True


@pytest.mark.django_db
def test_background_permanent_ignores_end_and_forces_background_policy(manager_form):
    admin, request, data, point, playlist = manager_form
    data.update(placement="background", is_permanent="on", playback_policy="", ends_at_0="bad-date", image_duration_seconds="12")
    form = admin.get_form(request)(data=data)
    assert form.is_valid(), form.errors
    assert form.instance.ends_at is None
    assert form.instance.playback_policy == "workday"
    assert "times_in_hour" not in form.instance.parameters
    assert form.instance.parameters["image_duration_seconds"] == 12


@pytest.mark.django_db
def test_temporary_background_requires_explicit_end(manager_form):
    admin, request, data, point, playlist = manager_form
    data.update(placement="background", playback_policy="", ends_at_0="", ends_at_1="")
    form = admin.get_form(request)(data=data)
    assert not form.is_valid() and "ends_at" in form.errors


@pytest.mark.django_db
def test_edit_preserves_unknown_settings_and_removes_old_schedule_keys(manager_form):
    admin, request, data, point, playlist = manager_form
    obj = Order.objects.create(name="Existing", placement="advertising", nomenclature=point, playlist=playlist,
        playback_policy="fixed_time", parameters={"times_in_hour": 2, "start_time": "10:00:00", "end_time": "11:00:00",
            "external_flag": {"keep": True}})
    form = admin.get_form(request, obj)(instance=obj, data=data)
    assert form.is_valid(), form.errors
    assert form.instance.parameters["external_flag"] == {"keep": True}
    assert form.instance.parameters["times_in_hour"] == 4
    assert "start_time" not in form.instance.parameters and "end_time" not in form.instance.parameters
    assert form.instance.nomenclature_id == point.pk


@pytest.mark.django_db
def test_admin_save_persists_typed_parameters_and_assigns_author(manager_form):
    admin, request, data, point, playlist = manager_form
    media = File(name="Prepared test clip", owner=request.user, source="tests/clip.mp4", type=1,
        hash="a" * 96, md5hash="a" * 32, sha256hash="a" * 64, size=1)
    # The test starts with prepared metadata; no upload or MinIO writes.
    File.objects.bulk_create([media])
    playlist.files.add(media)
    form = admin.get_form(request)(data=data)
    assert form.is_valid(), form.errors
    admin.save_model(request, form.instance, form, change=False)
    saved = Order.objects.get(pk=form.instance.pk)
    assert saved.owner_id == request.user.pk
    assert saved.parameters["times_in_hour"] == 4 and saved.parameters["weight"] == 70
    assert saved.nomenclature_id == point.pk


@pytest.mark.django_db
@pytest.mark.parametrize("extra,field", [({"times_in_hour": "0"}, "times_in_hour"),
    ({"playback_policy": "fixed_time", "start_time": "17:00", "end_time": "10:00"}, "end_time"),
    ({"playback_policy": "open_offset", "offset_minutes": "-1"}, "offset_minutes")])
def test_validation_points_to_a_visible_control(manager_form, extra, field):
    admin, request, data, point, playlist = manager_form
    form = admin.get_form(request)(data={**data, **extra})
    assert not form.is_valid()
    assert field in form.errors and "parameters" not in form.errors


@pytest.mark.django_db
def test_real_add_and_cancelled_change_pages_render_without_json(client, manager_form, super_user):
    admin, request, data, point, playlist = manager_form
    client.force_login(super_user)
    response = client.get(reverse("admin:orders_order_add"))
    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="id_parameters"' not in html
    assert 'id="id_times_in_hour"' in html and "order_form.js" in html
    obj = Order.objects.create(name="Cancelled", placement="advertising", nomenclature=point, playlist=playlist,
        is_active=False, status=3, parameters={"times_in_hour": 4})
    response = client.get(reverse("admin:orders_order_change", args=[obj.pk]))
    assert response.status_code == 200
    response = client.get(reverse("admin:orders_order_changelist"), {"delivery": "cancelled"})
    assert response.status_code == 200 and "Cancelled" in response.content.decode()


@pytest.mark.django_db
def test_legacy_event_parameters_are_preserved_and_new_event_is_not_offered(manager_form):
    admin, request, data, point, playlist = manager_form
    new_form = admin.get_form(request)()
    assert "event" not in dict(new_form.fields["playback_policy"].choices)
    obj = Order.objects.create(name="Legacy event", placement="advertising", nomenclature=point, playlist=playlist,
        playback_policy="event", suppress_background_audio=True, suppress_background_visual=True,
        parameters={"times_in_hour": 3, "event": "existing-trigger", "active_ad": True})
    form = admin.get_form(request, obj)(instance=obj, data=data)
    assert form.is_valid(), form.errors
    assert form.instance.playback_policy == "event"
    assert form.instance.parameters["event"] == "existing-trigger"
    assert form.instance.parameters["active_ad"] is True
    assert form.instance.parameters["times_in_hour"] == 3
