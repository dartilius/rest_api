import pytest

from nomenclatures.models import Nomenclature


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


@pytest.mark.django_db
def test_web_search_validates_price_range(anon_client):
    response = anon_client.post(
        "/api/nomenclatures/web/search/",
        data={"price_from": "100", "price_to": "10"},
        format="json",
    )

    assert response.status_code == 400
    assert "price_to" in response.json()
