"""Compatibility tests for statistic receipts in the legacy station endpoint."""

import json
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.test import Client

from nomenclatures.models import StatisticReceipt
from tasks.models import Task


@pytest.mark.django_db
def test_pending_tasks_reports_only_statistics_accepted_by_the_queue(
    client, nomenclature, django_capture_on_commit_callbacks
) -> None:
    statistic = {
        "music": [
            {
                "file": "music-file-1",
                "played": "2026-09-11 12:00:00",
                "length": 30,
            },
            {
                "file": "music-file-2",
                "played": "2026-09-11 12:01:00",
                "length": 30,
            },
        ]
    }
    url = f"/api/tasks/{nomenclature.id}/pending_tasks/"

    with (
        patch("nomenclatures.views.task.create_statistic.delay") as enqueue,
        django_capture_on_commit_callbacks(execute=True),
    ):
        response = client.post(
            url,
            data=json.dumps({"statistic": statistic}),
            content_type="application/json",
        )

    assert response.status_code == 200
    assert response.json()["statistics_accepted"] == {"music": 2}
    enqueue.assert_called_once_with("music", str(nomenclature.id), statistic["music"])


@pytest.mark.django_db
def test_pending_tasks_rejects_malformed_statistic(client, nomenclature) -> None:
    response = client.post(
        f"/api/tasks/{nomenclature.id}/pending_tasks/",
        data=json.dumps({"statistic": "not-an-object"}),
        content_type="application/json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_pending_tasks_deduplicates_events_with_receipt_ids(
    client, nomenclature, django_capture_on_commit_callbacks
) -> None:
    event = {
        "event_id": str(uuid4()),
        "file": "music-file-1",
        "played": "2026-09-12 12:00:00",
        "length": 30,
    }
    url = f"/api/tasks/{nomenclature.id}/pending_tasks/"

    with (
        patch("nomenclatures.views.task.create_statistic.delay") as enqueue,
        django_capture_on_commit_callbacks(execute=True),
    ):
        first = client.post(
            url,
            data=json.dumps({"statistic": {"music": [event]}}),
            content_type="application/json",
        )
        second = client.post(
            url,
            data=json.dumps({"statistic": {"music": [event]}}),
            content_type="application/json",
        )

    assert first.json()["statistics_accepted"] == {"music": 1}
    assert second.json()["statistics_accepted"] == {"music": 1}
    enqueue.assert_called_once_with("music", str(nomenclature.id), [event])
    assert StatisticReceipt.objects.filter(nomenclature=nomenclature).count() == 1


@pytest.mark.django_db
def test_pending_tasks_does_not_save_unchanged_station_inventory(
    client, nomenclature
) -> None:
    inventory = {"inventory_version": 1, "displays": [{"name": "Display 1"}]}
    nomenclature.hw_info = inventory
    nomenclature.save(update_fields=["hw_info"])

    with patch.object(nomenclature.__class__, "save") as save:
        response = client.post(
            f"/api/tasks/{nomenclature.id}/pending_tasks/",
            data=json.dumps({"hw_info": inventory, "version": nomenclature.version}),
            content_type="application/json",
        )

    assert response.status_code == 200
    save.assert_not_called()


@pytest.mark.django_db
def test_pending_tasks_saves_current_playback_state(client, nomenclature) -> None:
    runtime_state = {
        "mode": "ad",
        "current_ad": {"name": "Offer", "duration_seconds": 30},
        "background": [{"type": 0, "name": "music.mp3", "status": "пауза"}],
    }

    response = client.post(
        f"/api/tasks/{nomenclature.id}/pending_tasks/",
        data=json.dumps({"runtime_state": runtime_state}),
        content_type="application/json",
    )

    nomenclature.refresh_from_db()
    assert response.status_code == 200
    assert nomenclature.runtime_state == runtime_state


@pytest.mark.django_db
def test_pending_tasks_cannot_update_another_stations_task(
    client, nomenclature, nomenclature_1, user
) -> None:
    foreign_task = Task.objects.create(
        client=nomenclature_1,
        owner=user,
        type=17,
        parameters={},
    )

    response = client.post(
        f"/api/tasks/{nomenclature.id}/pending_tasks/",
        data=json.dumps({"task_status": {str(foreign_task.id): 2}}),
        content_type="application/json",
    )

    foreign_task.refresh_from_db()
    assert response.status_code == 200
    assert foreign_task.status == 0


@pytest.mark.django_db
def test_pending_tasks_rejects_invalid_task_status(client, nomenclature) -> None:
    response = client.post(
        f"/api/tasks/{nomenclature.id}/pending_tasks/",
        data=json.dumps({"task_status": {str(uuid4()): True}}),
        content_type="application/json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_actions_queues_typed_maintenance_command(admin_client, nomenclature) -> None:
    with patch("nomenclatures.views.task.maintenance_mode_task.delay") as enqueue:
        response = admin_client.post(
            f"/api/tasks/{nomenclature.id}/actions/",
            data={"task": "maintenance", "enabled": True, "reason": "Display repair"},
            format="json",
        )

    assert response.status_code == 200
    enqueue.assert_called_once()
    assert enqueue.call_args.args[:3] == (
        str(nomenclature.id),
        True,
        "Display repair",
    )


@pytest.mark.django_db
def test_actions_rejects_maintenance_without_reason(admin_client, nomenclature) -> None:
    response = admin_client.post(
        f"/api/tasks/{nomenclature.id}/actions/",
        data={"task": "maintenance", "enabled": True, "reason": ""},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_admin_queues_maintenance_mode_from_station_card(
    super_user, nomenclature
) -> None:
    client = Client()
    client.force_login(super_user)

    with patch("nomenclatures.admin.maintenance_mode_task.delay") as enqueue:
        response = client.post(
            f"/admin/nomenclatures/nomenclature/{nomenclature.id}/maintenance/",
            data={"enabled": "true", "reason": "Display repair"},
        )

    assert response.status_code == 302
    enqueue.assert_called_once_with(
        str(nomenclature.id),
        True,
        "Display repair",
        str(super_user.id),
    )


@pytest.mark.django_db
def test_admin_rejects_maintenance_entry_without_reason(
    super_user, nomenclature
) -> None:
    client = Client()
    client.force_login(super_user)

    with patch("nomenclatures.admin.maintenance_mode_task.delay") as enqueue:
        response = client.post(
            f"/admin/nomenclatures/nomenclature/{nomenclature.id}/maintenance/",
            data={"enabled": "true", "reason": ""},
        )

    assert response.status_code == 302
    enqueue.assert_not_called()
