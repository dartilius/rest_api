from datetime import time
from types import SimpleNamespace

import pytest

from brands.models import Brand
from counterparties.models import Counterparty
from nomenclatures.models import Nomenclature, TypeOfPlace
from nomenclatures.serializers import (
    NomenclatureWebLKSerializer,
    NomenclatureWebMapPlaceSerializer,
)


@pytest.mark.django_db
def test_web_search_returns_catalog_cards(anon_client, nomenclature):
    Nomenclature.objects.filter(pk=nomenclature.pk).update(
        for_web=True,
        old_catalog_slug="test-place",
    )

    response = anon_client.post(
        "/api/nomenclatures/web/search/",
        data={"search": "Test", "limit": 10},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["next_page"] is None
    assert payload["results"][0]["id"] == str(nomenclature.id)
    assert payload["results"][0]["oldCatalogSlug"] == "test-place"


@pytest.mark.django_db
def test_web_map_returns_compact_public_points(anon_client, nomenclature):
    Nomenclature.objects.filter(pk=nomenclature.pk).update(
        for_web=True,
        old_catalog_slug="test-place",
        slots_per_hour="2",
        worktime_start=time(9),
        worktime_end=time(20),
    )

    response = anon_client.post("/api/nomenclatures/web/map/", data={}, format="json")

    assert response.status_code == 200
    assert response.json()["results"] == [
        {
            "id": str(nomenclature.id),
            "name": "Test Nomenclature",
            "coordinates": None,
            "type_of_place": None,
            "brand": None,
            "facade": None,
            "per_day": 22.0,
            "old_slug": "test-place",
        }
    ]


@pytest.mark.django_db
def test_web_map_per_day_is_null_when_schedule_is_incomplete(nomenclature):
    assert NomenclatureWebMapPlaceSerializer(nomenclature).data["per_day"] is None


@pytest.mark.django_db
def test_web_map_per_day_calculates_slots_from_string_rate(nomenclature):
    Nomenclature.objects.filter(pk=nomenclature.pk).update(
        slots_per_hour="2",
        worktime_start=time(9),
        worktime_end=time(20),
    )
    nomenclature.refresh_from_db()

    assert NomenclatureWebMapPlaceSerializer(nomenclature).data["per_day"] == 22.0


def test_web_map_generates_name_from_place_brand_and_address():
    nomenclature = SimpleNamespace(
        name="Имя из модели",
        typeOfPlace=SimpleNamespace(abbreviation="ТЦ"),
        brand=SimpleNamespace(name="Планета"),
        address=SimpleNamespace(
            address=SimpleNamespace(
                city=SimpleNamespace(name="Красноярск"),
                street=SimpleNamespace(name="9 Мая"),
                house=SimpleNamespace(number="77"),
                building=None,
            )
        ),
    )

    assert NomenclatureWebMapPlaceSerializer().get_name(nomenclature) == (
        "ТЦ Планета, г. Красноярск, ул. 9 Мая, 77"
    )


@pytest.mark.django_db
def test_lk_krasrm_com_returns_active_web_nomenclatures_as_array(
    anon_client, nomenclature
):
    brand = Brand.objects.create(name="LK Brand", code1c="brand-1c")
    Nomenclature.objects.filter(pk=nomenclature.pk).update(
        for_web=True,
        brand=brand,
        code1c="nomenclature-1c",
    )
    inactive = Nomenclature.objects.create(
        name="Inactive", owner=nomenclature.owner, timezone="Etc/GMT-7",
        settings=nomenclature.settings, for_web=True, is_active=False,
    )
    not_for_web = Nomenclature.objects.create(
        name="Not for web", owner=nomenclature.owner, timezone="Etc/GMT-7",
        settings=nomenclature.settings, for_web=False,
    )

    response = anon_client.post(
        "/api/nomenclatures/web/lk-krasrm-com/", data={}, format="json"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() == [
        {
            "name": "LK Brand",
            "brand": {"code1c": "brand-1c", "name": "LK Brand"},
            "code1c": "nomenclature-1c",
            "broadcast": False,
        }
    ]
    assert inactive.pk != nomenclature.pk
    assert not_for_web.pk != nomenclature.pk


def test_lk_serializer_uses_the_map_name_algorithm():
    nomenclature = SimpleNamespace(
        name="Имя из модели",
        typeOfPlace=SimpleNamespace(abbreviation="ТЦ"),
        brand=SimpleNamespace(name="Планета"),
        address=SimpleNamespace(
            address=SimpleNamespace(
                city=SimpleNamespace(name="Красноярск"),
                street=SimpleNamespace(name="9 Мая"),
                house=SimpleNamespace(number="77"),
                building=None,
            )
        ),
    )

    assert NomenclatureWebLKSerializer().get_name(nomenclature) == (
        NomenclatureWebMapPlaceSerializer().get_name(nomenclature)
    )


@pytest.mark.django_db
def test_lk_krasrm_com_applies_search_broadcast_and_content_type_filters(
    anon_client, nomenclature, user
):
    broadcasting = Counterparty.objects.create(keyword="Broadcast", broadcast=True)
    not_broadcasting = Counterparty.objects.create(
        keyword="No broadcast", broadcast=False
    )
    Nomenclature.objects.filter(pk=nomenclature.pk).update(
        for_web=True, name="Matching audio", legalEntity=broadcasting,
        contentType="audio",
    )
    without_legal_entity = Nomenclature.objects.create(
        name="Matching video without entity", owner=user, timezone="Etc/GMT-7",
        settings=nomenclature.settings, for_web=True, contentType="video",
    )
    with_non_broadcasting_entity = Nomenclature.objects.create(
        name="Other video", owner=user, timezone="Etc/GMT-7",
        settings=nomenclature.settings, for_web=True, legalEntity=not_broadcasting,
        contentType="video",
    )

    response = anon_client.post(
        "/api/nomenclatures/web/lk-krasrm-com/",
        data={"search": "matching", "broadcast": True, "content_type": "audio"},
        format="json",
    )
    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Matching audio"]
    assert response.json()[0]["broadcast"] is True

    response = anon_client.post(
        "/api/nomenclatures/web/lk-krasrm-com/",
        data={"broadcast": False, "content_type": "video"}, format="json",
    )
    assert response.status_code == 200
    assert {item["name"] for item in response.json()} == {
        "Matching video without entity", "Other video"
    }
    assert {item["broadcast"] for item in response.json()} == {False}
    assert without_legal_entity.pk != with_non_broadcasting_entity.pk


@pytest.mark.django_db
def test_lk_krasrm_com_rejects_unknown_content_type(anon_client):
    response = anon_client.post(
        "/api/nomenclatures/web/lk-krasrm-com/",
        data={"content_type": "unknown"}, format="json",
    )

    assert response.status_code == 400
    assert "content_type" in response.json()


@pytest.mark.django_db
def test_web_search_validates_price_range(anon_client):
    response = anon_client.post(
        "/api/nomenclatures/web/search/",
        data={"price_from": "100", "price_to": "10"},
        format="json",
    )

    assert response.status_code == 400
    assert "price_to" in response.json()


@pytest.mark.django_db
def test_web_filter_options_are_mutually_dependent(anon_client, nomenclature, user):
    brand_a = Brand.objects.create(name="Brand A")
    brand_b = Brand.objects.create(name="Brand B")
    type_a = TypeOfPlace.objects.create(name="Type A")
    type_b = TypeOfPlace.objects.create(name="Type B")

    Nomenclature.objects.filter(pk=nomenclature.pk).update(
        for_web=True,
        brand=brand_a,
        typeOfPlace=type_a,
        contentType="audio",
    )
    Nomenclature.objects.create(
        name="Compatible place",
        owner=user,
        timezone="Etc/GMT-7",
        settings=nomenclature.settings,
        for_web=True,
        brand=brand_a,
        typeOfPlace=type_b,
        contentType="video",
    )
    Nomenclature.objects.create(
        name="Other brand place",
        owner=user,
        timezone="Etc/GMT-7",
        settings=nomenclature.settings,
        for_web=True,
        brand=brand_b,
        typeOfPlace=type_b,
        contentType="video",
    )

    response = anon_client.post(
        "/api/nomenclatures/web/filter-options/",
        data={"brand_ids": [str(brand_a.id)]},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert {option["id"] for option in payload["brands"]} == {
        str(brand_a.id),
        str(brand_b.id),
    }
    assert {option["id"] for option in payload["types_of_place"]} == {
        str(type_a.id),
        str(type_b.id),
    }
    assert payload["content_types"] == [
        {"value": "audio", "count": 1},
        {"value": "video", "count": 1},
    ]

    response = anon_client.post(
        "/api/nomenclatures/web/filter-options/",
        data={"content_types": ["audio"]},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["brands"] == [
        {"id": str(brand_a.id), "name": "Brand A", "count": 1}
    ]
    assert payload["types_of_place"] == [
        {"id": str(type_a.id), "name": "Type A", "count": 1}
    ]
