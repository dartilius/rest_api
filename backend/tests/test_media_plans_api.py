import re
from uuid import uuid4

import pytest


@pytest.mark.django_db
def test_owner_can_create_update_and_copy_a_media_plan(user_client, nomenclature):
    response = user_client.post(
        "/api/placement-orders/",
        {"nomenclature_ids": [str(nomenclature.id)]},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["name"].startswith("Медиаплан ")
    assert re.fullmatch(r"MP-\d{8}-[A-F0-9]{8}", response.data["plan_number"])
    assert response.data["revision"] == 1
    assert response.data["duration"] == 30

    plan_id = response.data["id"]
    plan_number = response.data["plan_number"]
    response = user_client.patch(
        f"/api/placement-orders/{plan_id}/",
        {"name": "Осенний план"},
        format="json",
        HTTP_IF_MATCH="1",
    )
    assert response.status_code == 200
    assert response.data["revision"] == 2

    response = user_client.patch(
        f"/api/placement-orders/{plan_id}/",
        {"nomenclature_ids": [str(nomenclature.id)]},
        format="json",
        HTTP_IF_MATCH="2",
    )
    assert response.status_code == 200
    assert response.data["revision"] == 3
    assert response.data["items"][0]["nomenclature"] == str(nomenclature.id)

    response = user_client.post(f"/api/placement-orders/{plan_id}/copy/", format="json")
    assert response.status_code == 201
    assert response.data["commercial_status"] == "new"
    assert response.data["plan_number"] != plan_number


@pytest.mark.django_db
def test_owner_update_of_unknown_media_plan_returns_not_found(user_client):
    response = user_client.patch(
        f"/api/placement-orders/{uuid4()}/",
        {"name": "План"},
        format="json",
        HTTP_IF_MATCH="1",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_media_plan_rejects_missing_or_stale_revision(user_client, user):
    from placement_order.models import PlacementOrder

    plan = PlacementOrder.objects.create(owner=user, duration=30)
    url = f"/api/placement-orders/{plan.id}/"

    assert user_client.patch(url, {"name": "changed"}, format="json").status_code == 428
    stale = user_client.patch(url, {"name": "changed"}, format="json", HTTP_IF_MATCH="0")
    assert stale.status_code == 409
    assert stale.data["revision"] == 1


@pytest.mark.django_db
def test_feedback_is_public_create_only(client):
    assert client.get("/api/feedback/").status_code == 405
