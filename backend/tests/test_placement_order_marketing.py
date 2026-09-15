from datetime import timedelta

import pytest
from django.utils import timezone

from placement_order.marketing import validate_attribution_payload
from placement_order.models import PlacementOrder


ATTRIBUTION = {
    "version": 1,
    "first_touch": {
        "landing_path": "/nomenclatures",
        "referrer_host": "yandex.ru",
        "utm_source": "yandex",
        "utm_medium": "cpc",
        "utm_campaign": "indoor_krasnoyarsk",
    },
    "last_touch": {"landing_path": "/nomenclatures"},
}


@pytest.mark.django_db
def test_commercial_status_sets_timestamp_only_on_first_transition(manager_user):
    order = PlacementOrder.objects.create(owner=manager_user, duration=2)

    order.commercial_status = "qualified"
    order.save()
    order.refresh_from_db()
    first_qualified_at = order.qualified_at

    order.commercial_status = "new"
    order.save()
    order.commercial_status = "qualified"
    order.save()
    order.refresh_from_db()

    assert first_qualified_at is not None
    assert order.qualified_at == first_qualified_at


def test_attribution_rejects_full_urls():
    invalid_attribution = {
        **ATTRIBUTION,
        "first_touch": {"landing_path": "https://example.test/?email=user@example.test"},
    }

    with pytest.raises(ValueError):
        validate_attribution_payload(invalid_attribution)


@pytest.mark.django_db
def test_manager_can_update_status_and_read_aggregate_report(manager_user, manager_client):
    booked_order = PlacementOrder.objects.create(
        owner=manager_user,
        duration=2,
        attribution=ATTRIBUTION,
    )
    PlacementOrder.objects.create(
        owner=manager_user,
        duration=2,
        attribution=ATTRIBUTION,
    )

    response = manager_client.patch(
        f"/api/placement-orders/{booked_order.id}/commercial-status/",
        {"commercial_status": "booked"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["booked_at"] is not None

    today = timezone.localdate()
    response = manager_client.get(
        "/api/marketing/placement-orders/report",
        {"from": today.isoformat(), "to": (today + timedelta(days=1)).isoformat()},
    )

    assert response.status_code == 200
    assert response.data["created"] == 2
    assert response.data["by_status"]["booked"] == 1
    assert response.data["by_status"]["new"] == 1
    assert response.data["by_source"] == [
        {"source": "yandex / cpc", "created": 2, "booked": 1, "booked_rate": 0.5}
    ]
