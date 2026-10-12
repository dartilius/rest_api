import pytest
from django.contrib import admin
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from nomenclatures.models import StationCredential
from nomenclatures.player_v2.admin import StationVolumeCommandForm


@pytest.mark.django_db
def test_empty_command_form_does_not_read_station_catalog():
    with CaptureQueriesContext(connection) as queries:
        form = StationVolumeCommandForm()
    assert len(queries) == 0
    assert list(form.fields["audio_device_id"].choices) == [("", "Сначала выберите точку вещания")]


@pytest.mark.django_db
def test_command_form_loads_devices_script_after_django_jquery():
    script_paths = StationVolumeCommandForm().media._js
    assert script_paths.index("admin/js/jquery.init.js") < script_paths.index(
        "nomenclatures/station_devices.js"
    )


@pytest.mark.django_db
def test_command_devices_are_scoped_to_selected_station(nomenclature, nomenclature_1):
    for station, device in ((nomenclature, "this-device"), (nomenclature_1, "other-device")):
        station.station_capabilities = {"audio": {"devices": [{"id": device}]}}
        station.save(update_fields=["station_capabilities"])
    with CaptureQueriesContext(connection) as queries:
        form = StationVolumeCommandForm(data={"nomenclature": str(nomenclature.pk)})
    assert len(queries) == 1
    assert [value for value, _ in form.fields["audio_device_id"].choices] == ["", "this-device"]


@pytest.mark.django_db
def test_devices_endpoint_requires_command_add_permission(client, super_user, nomenclature):
    nomenclature.station_capabilities = {"displays": [{"id": "screen", "name": "Screen"}]}
    nomenclature.save(update_fields=["station_capabilities"])
    client.force_login(super_user)
    url = reverse("admin:nomenclatures_stationcommandv2_devices")
    response = client.get(url, {"station": str(nomenclature.pk)})
    assert response.status_code == 200
    assert response.json()["displays"][1][0] == "screen"
    super_user.is_superuser = False
    super_user.save(update_fields=["is_superuser"])
    assert client.get(url, {"station": str(nomenclature.pk)}).status_code == 403


@pytest.mark.django_db
def test_devices_endpoint_explains_missing_player_inventory(client, super_user, nomenclature):
    nomenclature.station_capabilities = None
    nomenclature.save(update_fields=["station_capabilities"])
    client.force_login(super_user)

    response = client.get(
        reverse("admin:nomenclatures_stationcommandv2_devices"),
        {"station": str(nomenclature.pk)},
    )

    assert response.status_code == 200
    assert response.json()["audio"] == [["", "Player ещё не передал список аудиоустройств"]]
    assert response.json()["displays"] == [["", "Player ещё не передал список мониторов"]]


@pytest.mark.django_db
def test_empty_volume_choices_are_form_errors(nomenclature):
    form = StationVolumeCommandForm(data={
        "nomenclature": str(nomenclature.pk), "setting_group": "volume",
        "day": "mon", "source": "", "channel": "", "volume": 0,
    })
    assert not form.is_valid()
    assert "source" in form.errors and "channel" in form.errors
    assert "volume" not in form.errors


@pytest.mark.django_db
def test_invalid_saved_settings_are_reported_before_save(nomenclature):
    nomenclature.settings = {}
    nomenclature.save(update_fields=["settings"])
    form = StationVolumeCommandForm(data={
        "nomenclature": str(nomenclature.pk), "setting_group": "volume",
        "day": "mon", "source": "background", "channel": "left", "volume": 50,
    })
    assert not form.is_valid()
    assert form.non_field_errors()


@pytest.mark.django_db
def test_bulk_rotation_does_not_discard_station_tokens(nomenclature, nomenclature_1, monkeypatch):
    first = StationCredential.objects.create(nomenclature=nomenclature, token_hash="a" * 64)
    second = StationCredential.objects.create(nomenclature=nomenclature_1, token_hash="b" * 64)
    model_admin = admin.site._registry[StationCredential]
    monkeypatch.setattr(model_admin, "message_user", lambda *args, **kwargs: None)
    model_admin.rotate_tokens(RequestFactory().post("/admin/"), StationCredential.objects.all())
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.token_hash == "a" * 64
    assert second.token_hash == "b" * 64
