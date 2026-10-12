"""Admin switch -> real typed task, replacing only the Celery broker."""

from unittest.mock import patch

import pytest
from django.test import Client

from nomenclatures.tasks import maintenance_mode_task
from tasks.models import Task


@pytest.mark.django_db
@pytest.mark.parametrize("enabled", [True, False])
def test_admin_service_switch_creates_boolean_task_for_both_directions(
    super_user, nomenclature, enabled,
):
    operator = Client()
    operator.force_login(super_user)
    with patch(
        "nomenclatures.admin.maintenance_mode_task.delay",
        side_effect=lambda *args: maintenance_mode_task.run(*args),
    ):
        response = operator.post(
            f"/admin/nomenclatures/nomenclature/{nomenclature.pk}/maintenance/",
            data={"enabled": "true" if enabled else "false",
                  "reason": "Test service entry" if enabled else ""},
        )
    assert response.status_code == 302
    task = Task.objects.get(client=nomenclature, type=17)
    assert task.parameters["command"] == "maintenance_mode"
    assert task.parameters["enabled"] is enabled
    assert task.owner_id == super_user.pk
