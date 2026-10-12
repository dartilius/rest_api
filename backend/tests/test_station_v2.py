"""Security and delivery contracts for the isolated Player v2 endpoint."""

from copy import deepcopy
import hashlib

import pytest
from django.contrib import admin
from django.test import RequestFactory
from django.utils import timezone

from nomenclatures.admin import NomenclatureAdmin, StationInstallationInline
from nomenclatures.models import StationCommandV2, StationCredential, StationInstallation
from nomenclatures.player_v2.admin import (
    StationCommandV2Admin,
    StationInstallationAdmin,
    StationVolumeCommandForm,
)
from nomenclatures.player_v2.credentials import hash_station_token, issue_station_token


def _headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Station {token}"}


def _jwt_headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"access_token {token}"}


def _station_capabilities() -> dict:
    return {
        "inventory_version": 2,
        "system": {"os": "Windows"},
        "displays": [
            {
                "id": "0",
                "name": "Display 1",
                "is_primary": True,
                "width": 1920,
                "height": 1080,
                "supported_rotations": [0, 90, 180, 270],
            }
        ],
        "audio": {
            "devices": [{"id": "default", "name": "System", "is_default": True}],
            "selected_device": {"id": "default", "name": "System", "is_default": True},
        },
    }


@pytest.mark.django_db
def test_admin_audio_device_form_queues_only_a_published_device(nomenclature):
    nomenclature.station_capabilities = _station_capabilities()
    nomenclature.save(update_fields=["station_capabilities"])

    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "audio_device",
            "day": "mon",
            "audio_device_id": "default",
        }
    )

    assert form.is_valid(), form.errors
    command = form.save()
    assert command.kind == "select_audio_device"
    assert command.body == {"device_id": "default"}


@pytest.mark.django_db
def test_admin_audio_device_form_rejects_a_device_from_another_station(nomenclature):
    nomenclature.station_capabilities = _station_capabilities()
    nomenclature.save(update_fields=["station_capabilities"])

    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "audio_device",
            "day": "mon",
            "audio_device_id": "unknown-device",
        }
    )

    assert not form.is_valid()
    assert "audio_device_id" in form.errors


@pytest.mark.django_db
def test_admin_display_form_queues_only_a_published_display(nomenclature):
    nomenclature.station_capabilities = _station_capabilities()
    nomenclature.save(update_fields=["station_capabilities"])

    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "display",
            "day": "mon",
            "display_id": "0",
        }
    )

    assert form.is_valid(), form.errors
    command = form.save()
    assert command.kind == "select_display"
    assert command.body == {"display_id": "0"}


@pytest.mark.django_db
def test_admin_display_form_rejects_an_unknown_display(nomenclature):
    nomenclature.station_capabilities = _station_capabilities()
    nomenclature.save(update_fields=["station_capabilities"])

    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "display",
            "day": "mon",
            "display_id": "99",
        }
    )

    assert not form.is_valid()
    assert "display_id" in form.errors


@pytest.mark.django_db
def test_admin_visual_output_form_queues_station_wide_rotation(nomenclature):
    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "visual_output",
            "day": "mon",
            "visual_output_rotation": "90",
        }
    )

    assert form.is_valid(), form.errors
    command = form.save()
    assert command.kind == "set_visual_output"
    assert command.body == {"rotation": 90}


def test_admin_visual_output_angle_field_is_visible_when_creating_command():
    command_admin = StationCommandV2Admin(StationCommandV2, admin.site)
    fieldsets = command_admin.get_fieldsets(RequestFactory().get("/admin/"))

    displayed_fields = {
        field
        for _title, options in fieldsets
        for field in options["fields"]
    }
    assert "visual_output_rotation" in displayed_fields


def test_auto_bound_installations_are_visible_in_admin():
    """Автоматическая привязка не должна оставаться скрытой от оператора."""
    installation_admin = admin.site._registry[StationInstallation]

    assert isinstance(installation_admin, StationInstallationAdmin)
    assert StationInstallationInline in NomenclatureAdmin.inlines


@pytest.mark.django_db
def test_player_reports_confirmed_visual_output_separately(client, nomenclature):
    token = "visual-output-station-token"
    StationCredential.objects.create(
        nomenclature=nomenclature,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )

    response = client.post(
        "/api/station/v2/sync/",
        data='{"applied_visual_output": {"rotation": 270}}',
        content_type="application/json",
        **_headers(token),
    )

    assert response.status_code == 200
    nomenclature.refresh_from_db()
    assert nomenclature.visual_output_settings == {"rotation": 270}


@pytest.mark.django_db
def test_player_cannot_report_an_unsupported_visual_rotation(client, nomenclature):
    token = "invalid-visual-output-station-token"
    StationCredential.objects.create(
        nomenclature=nomenclature,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )

    response = client.post(
        "/api/station/v2/sync/",
        data='{"applied_visual_output": {"rotation": 45}}',
        content_type="application/json",
        **_headers(token),
    )

    assert response.status_code == 400
    nomenclature.refresh_from_db()
    assert nomenclature.visual_output_settings is None


@pytest.mark.django_db
def test_issued_station_token_is_hash_only_and_rotation_invalidates_previous_token(nomenclature):
    credential = StationCredential.objects.create(nomenclature=nomenclature, token_hash=hash_station_token("initial"))

    first_token = issue_station_token(credential)
    credential.refresh_from_db()
    assert credential.token_hash == hash_station_token(first_token)
    assert credential.token_hash != first_token

    second_token = issue_station_token(credential)
    credential.refresh_from_db()
    assert second_token != first_token
    assert credential.token_hash == hash_station_token(second_token)


@pytest.mark.django_db
def test_station_token_sees_only_its_pending_commands(client, nomenclature, nomenclature_1):
    token = "station-test-token"
    StationCredential.objects.create(
        nomenclature=nomenclature,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )
    own = StationCommandV2.objects.create(
        nomenclature=nomenclature, body={"base_revision": 0, "operations": []},
    )
    StationCommandV2.objects.create(
        nomenclature=nomenclature_1, body={"base_revision": 1, "operations": []},
    )

    response = client.post("/api/station/v2/sync/", data="{}", content_type="application/json", **_headers(token))

    assert response.status_code == 200
    assert response.json()["commands"] == [{
        "command_id": str(own.command_id), "kind": "apply_settings_patch",
        "base_revision": 0, "operations": [],
    }]
    own.refresh_from_db()
    assert own.delivered_at is not None


@pytest.mark.django_db
def test_station_v2_rejects_missing_or_invalid_token(client):
    assert client.post("/api/station/v2/sync/", data="{}", content_type="application/json").status_code == 401
    assert client.post("/api/station/v2/sync/", data="{}", content_type="application/json", **_headers("wrong")).status_code == 401


@pytest.mark.django_db
def test_authenticated_admin_can_bind_station_and_use_issued_token(client, nomenclature, superuser_token):
    response = client.post(
        "/api/station/v2/bind/",
        data={"nomenclature_id": str(nomenclature.pk)},
        content_type="application/json",
        **_jwt_headers(superuser_token["access"]),
    )

    assert response.status_code == 200
    token = response.json()["station_token"]
    installation_id = response.json()["installation_id"]
    assert StationInstallation.objects.filter(pk=installation_id, nomenclature=nomenclature).exists()
    assert client.post(
        "/api/station/v2/sync/",
        data="{}",
        content_type="application/json",
        **_headers(token),
    ).status_code == 200


@pytest.mark.django_db
def test_rebinding_one_installation_revokes_its_previous_station_token(
    client, nomenclature, nomenclature_1, superuser_token
):
    initial = client.post(
        "/api/station/v2/bind/",
        data={"nomenclature_id": str(nomenclature.pk)},
        content_type="application/json",
        **_jwt_headers(superuser_token["access"]),
    ).json()

    moved = client.post(
        "/api/station/v2/bind/",
        data={
            "nomenclature_id": str(nomenclature_1.pk),
            "installation_id": initial["installation_id"],
        },
        content_type="application/json",
        **_jwt_headers(superuser_token["access"]),
    )

    assert moved.status_code == 200
    replacement = moved.json()
    assert replacement["installation_id"] == initial["installation_id"]
    assert replacement["station_token"] != initial["station_token"]
    assert client.post(
        "/api/station/v2/sync/",
        data="{}",
        content_type="application/json",
        **_headers(initial["station_token"]),
    ).status_code == 401
    assert client.post(
        "/api/station/v2/sync/",
        data="{}",
        content_type="application/json",
        **_headers(replacement["station_token"]),
    ).status_code == 200


@pytest.mark.django_db
def test_receipt_changes_only_own_pending_command(client, nomenclature):
    token = "station-test-token"
    StationCredential.objects.create(nomenclature=nomenclature, token_hash=hashlib.sha256(token.encode()).hexdigest())
    command = StationCommandV2.objects.create(nomenclature=nomenclature, body={})
    response = client.post("/api/station/v2/sync/", data={"receipts": [{"command_id": str(command.command_id), "status": "applied", "result": {"saved_revision": 1}}]}, content_type="application/json", **_headers(token))
    assert response.status_code == 200
    command.refresh_from_db()
    assert command.status == StationCommandV2.Status.APPLIED
    assert command.result == {"saved_revision": 1}


@pytest.mark.django_db
def test_station_v2_rejects_invalid_receipt_and_preserves_command(client, nomenclature):
    token = "station-test-token"
    StationCredential.objects.create(nomenclature=nomenclature, token_hash=hashlib.sha256(token.encode()).hexdigest())
    command = StationCommandV2.objects.create(nomenclature=nomenclature, body={})

    response = client.post(
        "/api/station/v2/sync/",
        data={"receipts": [{"command_id": "not-a-uuid", "status": "applied"}]},
        content_type="application/json",
        **_headers(token),
    )

    assert response.status_code == 400
    command.refresh_from_db()
    assert command.status == StationCommandV2.Status.PENDING


@pytest.mark.django_db
def test_command_body_cannot_override_protocol_metadata(client, nomenclature):
    token = "station-test-token"
    StationCredential.objects.create(nomenclature=nomenclature, token_hash=hashlib.sha256(token.encode()).hexdigest())
    command = StationCommandV2.objects.create(
        nomenclature=nomenclature,
        kind="apply_settings_patch",
        body={"command_id": "spoofed", "kind": "spoofed"},
    )

    response = client.post("/api/station/v2/sync/", data="{}", content_type="application/json", **_headers(token))

    assert response.status_code == 200
    assert response.json()["commands"] == [{
        "command_id": str(command.command_id),
        "kind": "apply_settings_patch",
    }]


@pytest.mark.django_db
def test_admin_volume_form_queues_one_named_channel_change(nomenclature):
    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "volume",
            "day": "tue",
            "source": "advertisement",
            "channel": "right",
            "volume": 42,
        }
    )

    assert form.is_valid(), form.errors
    command = form.save()
    assert command.kind == "apply_settings_patch"
    assert command.body == {
        "base_revision": 0,
        "operations": [
            {
                "op": "set",
                "path": "/days/tue/default_volume/advertisement/right",
                "value": 42,
            }
        ],
    }


@pytest.mark.django_db
def test_admin_volume_form_blocks_second_pending_settings_change(nomenclature):
    StationCommandV2.objects.create(nomenclature=nomenclature, body={})
    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "volume",
            "day": "wed",
            "source": "background",
            "channel": "left",
            "volume": 20,
        }
    )

    assert not form.is_valid()
    assert "ожидающее изменение" in form.non_field_errors()[0]


@pytest.mark.django_db
def test_admin_volume_form_can_apply_one_channel_to_all_days(nomenclature):
    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "volume",
            "day": "mon",
            "all_days": "on",
            "source": "background",
            "channel": "right",
            "volume": 55,
        }
    )

    assert form.is_valid(), form.errors
    command = form.save()
    operations = command.body["operations"]
    assert len(operations) == 7
    assert [operation["path"].split("/")[2] for operation in operations] == [
        "mon", "tue", "wed", "thu", "fri", "sat", "sun"
    ]
    assert all(operation["value"] == 55 for operation in operations)


@pytest.mark.django_db
def test_station_command_admin_saves_command_without_credential_fields(nomenclature):
    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "volume",
            "day": "fri",
            "source": "background",
            "channel": "left",
            "volume": 10,
        }
    )
    assert form.is_valid(), form.errors
    command = form.save(commit=False)

    command_admin = admin.site._registry[StationCommandV2]
    command_admin.save_model(RequestFactory().post("/admin/"), command, form, False)

    assert command.pk is not None
    assert command.body["operations"][0]["value"] == 10


@pytest.mark.django_db
def test_admin_background_form_changes_only_selected_setting_for_all_days(nomenclature):
    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "background",
            "day": "mon",
            "all_days": "on",
            "background_setting": "img_duration",
            "image_duration": 12,
        }
    )

    assert form.is_valid(), form.errors
    command = form.save()

    assert command.body == {
        "base_revision": 0,
        "operations": [
            {
                "op": "set",
                "path": f"/days/{day}/background/img_duration",
                "value": 12,
            }
            for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
        ],
    }


@pytest.mark.django_db
def test_admin_worktime_form_queues_one_operation_per_day(nomenclature):
    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "worktime",
            "day": "mon",
            "all_days": "on",
            "worktime_start": "08:30",
            "worktime_end": "21:15",
        }
    )

    assert form.is_valid(), form.errors
    command = form.save()
    assert command.body["operations"] == [
        {
            "op": "set",
            "path": f"/days/{day}/worktime",
            "value": "08:30:00-21:15:00",
        }
        for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
    ]


@pytest.mark.django_db
def test_player_snapshot_updates_original_settings_field(client, nomenclature):
    token = "station-test-token"
    StationCredential.objects.create(
        nomenclature=nomenclature,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )
    desired_settings = deepcopy(nomenclature.settings)
    applied_settings = deepcopy(desired_settings)
    applied_settings["mon"]["default_volume"][0] = 71

    response = client.post(
        "/api/station/v2/sync/",
        data={"applied_settings": applied_settings, "applied_settings_revision": 4},
        content_type="application/json",
        **_headers(token),
    )

    assert response.status_code == 200
    nomenclature.refresh_from_db()
    assert nomenclature.settings == applied_settings
    assert nomenclature.applied_settings_revision == 4
    assert nomenclature.player_sync_state.applied_settings is None
    assert not nomenclature.runtime_state or "applied_settings" not in nomenclature.runtime_state


@pytest.mark.django_db
def test_admin_command_keeps_confirmed_settings_until_player_reports_change(nomenclature):
    original_settings = deepcopy(nomenclature.settings)
    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "volume",
            "day": "tue",
            "source": "advertisement",
            "channel": "right",
            "volume": 42,
        }
    )

    assert form.is_valid(), form.errors
    form.save()

    nomenclature.refresh_from_db()
    assert nomenclature.settings == original_settings


@pytest.mark.django_db
def test_admin_command_uses_last_reported_player_revision(nomenclature):
    nomenclature.applied_settings_revision = 7
    nomenclature.save(update_fields=["applied_settings_revision"])
    form = StationVolumeCommandForm(
        data={
            "nomenclature": str(nomenclature.pk),
            "setting_group": "volume",
            "day": "wed",
            "source": "background",
            "channel": "left",
            "volume": 20,
        }
    )

    assert form.is_valid(), form.errors
    command = form.save()
    assert command.body["base_revision"] == 7


@pytest.mark.django_db
def test_admin_delivery_state_distinguishes_delivery_from_receipt(nomenclature):
    command = StationCommandV2.objects.create(nomenclature=nomenclature, body={})
    command_admin = admin.site._registry[StationCommandV2]

    assert command_admin.delivery_state(command) == "Ожидает отправки"

    command.delivered_at = timezone.now()
    assert command_admin.delivery_state(command) == "Доставлена, ждёт подтверждения"

    command.status = StationCommandV2.Status.APPLIED
    assert command_admin.delivery_state(command) == "Применена"


@pytest.mark.django_db
def test_station_capabilities_are_saved_separately_from_settings_and_runtime(client, nomenclature):
    token = "station-test-token"
    StationCredential.objects.create(
        nomenclature=nomenclature,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )
    capabilities = _station_capabilities()

    response = client.post(
        "/api/station/v2/sync/",
        data={"station_capabilities": capabilities},
        content_type="application/json",
        **_headers(token),
    )

    assert response.status_code == 200
    nomenclature.refresh_from_db()
    assert nomenclature.station_capabilities == capabilities
    assert nomenclature.runtime_state is None


@pytest.mark.django_db
def test_station_capabilities_accept_startup_without_selected_audio_device(client, nomenclature):
    """The Player may poll before its asynchronous audio inventory is ready."""
    token = "station-startup-inventory-token"
    StationCredential.objects.create(
        nomenclature=nomenclature,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )
    capabilities = _station_capabilities()
    capabilities["audio"]["selected_device"] = None

    response = client.post(
        "/api/station/v2/sync/",
        data={"station_capabilities": capabilities},
        content_type="application/json",
        **_headers(token),
    )

    assert response.status_code == 200
    nomenclature.refresh_from_db()
    assert nomenclature.station_capabilities == capabilities


@pytest.mark.django_db
@pytest.mark.parametrize(
    "audio",
    (
        {"devices": []},
        {"devices": [], "selected_device": None, "unexpected": True},
    ),
)
def test_station_capabilities_keep_audio_schema_strict(client, nomenclature, audio):
    token = "station-invalid-audio-inventory-token"
    StationCredential.objects.create(
        nomenclature=nomenclature,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )
    capabilities = _station_capabilities()
    capabilities["audio"] = audio

    response = client.post(
        "/api/station/v2/sync/",
        data={"station_capabilities": capabilities},
        content_type="application/json",
        **_headers(token),
    )

    assert response.status_code == 400
    nomenclature.refresh_from_db()
    assert nomenclature.station_capabilities is None


@pytest.mark.django_db
def test_station_capabilities_reject_hardware_telemetry(client, nomenclature):
    token = "station-test-token"
    StationCredential.objects.create(
        nomenclature=nomenclature,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
    )
    capabilities = _station_capabilities()
    capabilities["system"]["machine"] = "AMD64"

    response = client.post(
        "/api/station/v2/sync/",
        data={"station_capabilities": capabilities},
        content_type="application/json",
        **_headers(token),
    )

    assert response.status_code == 400
    nomenclature.refresh_from_db()
    assert nomenclature.station_capabilities is None
