from types import SimpleNamespace

import pytest

from nomenclatures.models import Nomenclature
from nomenclatures.serializers import NomenclatureWebMapPlaceSerializer


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
            "old_slug": "test-place",
        }
    ]


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
def test_web_search_validates_price_range(anon_client):
    response = anon_client.post(
        "/api/nomenclatures/web/search/",
        data={"price_from": "100", "price_to": "10"},
        format="json",
    )

    assert response.status_code == 400
    assert "price_to" in response.json()
