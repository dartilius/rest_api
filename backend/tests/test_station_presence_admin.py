"""Presence is loaded per page without hiding inactive stations or claiming air."""

from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.contrib.admin.sites import site
from django.urls import reverse
from django.utils import timezone

from nomenclatures.models import Nomenclature


@pytest.mark.django_db
def test_station_list_batches_presence_and_includes_inactive(
    client, super_user, nomenclature, nomenclature_1, monkeypatch
):
    Nomenclature.objects.filter(pk=nomenclature_1.pk).update(is_active=False)
    moment = timezone.now()
    loads = []

    def load(ids):
        ids = list(ids)
        loads.append(ids)
        return {
            str(nomenclature.pk): {"status": "fresh", "last_seen": moment},
            str(nomenclature_1.pk): {"status": "stale", "last_seen": moment - timedelta(minutes=5)},
        }

    monkeypatch.setattr("nomenclatures.admin.load_station_presence", load)
    single = Mock(side_effect=AssertionError("list must not read Redis per row"))
    monkeypatch.setattr("nomenclatures.admin.get_station_presence", single)
    client.force_login(super_user)

    response = client.get(reverse("admin:nomenclatures_nomenclature_changelist"))

    assert response.status_code == 200
    assert len(loads) == 1
    assert set(loads[0]) == {nomenclature.pk, nomenclature_1.pk}
    assert response.context["cl"].result_count == 2
    content = response.content.decode()
    assert "Связь подтверждена" in content
    assert "Данные о связи устарели" in content
    assert "Последняя синхронизация" in content
    single.assert_not_called()


@pytest.mark.django_db
def test_station_list_loads_presence_for_the_current_page_only(
    client, super_user, nomenclature, nomenclature_1, monkeypatch
):
    model_admin = site._registry[Nomenclature]
    monkeypatch.setattr(model_admin, "list_per_page", 1)
    loads = []

    def load(ids):
        ids = list(ids)
        loads.append(ids)
        return {str(station_id): {"status": "unknown", "last_seen": None} for station_id in ids}

    monkeypatch.setattr("nomenclatures.admin.load_station_presence", load)
    monkeypatch.setattr(
        "nomenclatures.admin.get_station_presence",
        Mock(side_effect=AssertionError("list must use the batch result")),
    )
    client.force_login(super_user)

    response = client.get(reverse("admin:nomenclatures_nomenclature_changelist"))

    assert response.status_code == 200
    assert response.context["cl"].result_count == 2
    assert len(loads) == 1
    assert len(loads[0]) == 1
    assert loads[0][0] in {nomenclature.pk, nomenclature_1.pk}


@pytest.mark.django_db
@pytest.mark.parametrize("status,label", [
    ("fresh", "Связь подтверждена"),
    ("stale", "Данные о связи устарели"),
    ("unknown", "Связь неизвестна"),
])
def test_station_card_shows_connection_without_claiming_playback(
    nomenclature, monkeypatch, status, label
):
    last_seen = None if status == "unknown" else timezone.now()
    lookup = Mock(return_value={"status": status, "last_seen": last_seen})
    monkeypatch.setattr("nomenclatures.admin.get_station_presence", lookup)

    rendered = str(site._registry[Nomenclature].player_v2_connection(nomenclature))

    assert label in rendered
    assert "В эфире" not in rendered
    lookup.assert_called_once_with(nomenclature.pk)
