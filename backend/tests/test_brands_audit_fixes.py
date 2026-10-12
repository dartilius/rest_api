from types import SimpleNamespace

import pytest
from django.contrib import admin
from rest_framework.test import APIRequestFactory, force_authenticate

from brands.admin import BrandAdmin
from brands.documents import BrandDocument
from brands.models import Brand
from brands.views import BrandViewSet, get_brand_min_price_qs
from nomenclatures.models import Nomenclature


@pytest.mark.django_db
def test_brand_min_price_uses_only_published_active_nomenclatures(user, nomenclature):
    brand = Brand.objects.create(name="Price brand")
    nomenclature.brand = brand
    nomenclature.for_web = True
    nomenclature.pricePerMonth = 100
    nomenclature.save()
    Nomenclature.objects.create(
        name="Hidden point",
        owner=user,
        timezone="Etc/GMT-7",
        settings=nomenclature.settings,
        brand=brand,
        for_web=False,
        pricePerMonth=1,
    )

    annotated_brand = get_brand_min_price_qs(Brand.objects.filter(pk=brand.pk)).get()

    assert annotated_brand.min_price == 100


@pytest.mark.django_db
def test_brand_list_returns_total_min_price(user, nomenclature):
    brand = Brand.objects.create(name="List price brand")
    nomenclature.brand = brand
    nomenclature.for_web = True
    nomenclature.pricePerMonth = 100
    nomenclature.save()
    Nomenclature.objects.create(
        name="Lower public point",
        owner=user,
        timezone="Etc/GMT-7",
        settings=nomenclature.settings,
        brand=brand,
        for_web=True,
        pricePerMonth=50,
    )

    request = APIRequestFactory().get("/api/brands/")
    response = BrandViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert response.data["min_price"] == 50


@pytest.mark.django_db
def test_brand_nomenclatures_action_avoids_per_item_queries(user, nomenclature, django_assert_num_queries):
    brand = Brand.objects.create(name="Catalog brand")
    nomenclature.brand = brand
    nomenclature.for_web = True
    nomenclature.save()
    for index in range(4):
        Nomenclature.objects.create(
            name=f"Catalog point {index}",
            owner=user,
            timezone="Etc/GMT-7",
            settings=nomenclature.settings,
            brand=brand,
            for_web=True,
        )

    request = APIRequestFactory().get(f"/api/brands/{brand.id}/nomenclatures/")
    view = BrandViewSet.as_view({"get": "nomenclatures"})

    with django_assert_num_queries(3):
        response = view(request, id_or_code1c=str(brand.id))

    assert response.status_code == 200
    assert len(response.data) == 5


@pytest.mark.django_db
def test_unpin_logo_accepts_code1c_and_empty_logo(user):
    brand = Brand.objects.create(name="Empty logo", code1c="legacy-brand-code")
    request = APIRequestFactory().post("/api/brands/legacy-brand-code/unpin_logo/")
    force_authenticate(request, user=user)
    view = BrandViewSet.as_view({"post": "unpin_logo"})

    response = view(request, id_or_code1c=brand.code1c)

    assert response.status_code == 204
    brand.refresh_from_db()
    assert not brand.logotype


def test_opensearch_query_uses_opensearch_dsl_q(monkeypatch):
    class SearchStub:
        query_object = None

        def filter(self, *args, **kwargs):
            return self

        def query(self, query):
            self.query_object = query
            return self

        def extra(self, **kwargs):
            return self

        def execute(self):
            return [SimpleNamespace(meta=SimpleNamespace(id="brand-id"))]

    search = SearchStub()
    monkeypatch.setattr(BrandDocument, "search", classmethod(lambda cls: search))

    assert BrandViewSet()._opensearch_brand_ids("test") == ["brand-id"]
    assert search.query_object.to_dict() == {
        "bool": {
            "should": [
                {
                    "multi_match": {
                        "query": "test",
                        "fields": [
                            "name^3",
                            "name.autocomplete^2",
                            "description",
                            "description.autocomplete",
                        ],
                        "fuzziness": "AUTO",
                        "type": "best_fields",
                    },
                },
                {"prefix": {"code1c": {"value": "test"}}},
                {"prefix": {"slug": {"value": "test"}}},
            ],
        },
    }


@pytest.mark.django_db
def test_brand_admin_list_uses_single_annotated_query(rf, django_assert_num_queries):
    Brand.objects.create(name="First brand")
    Brand.objects.create(name="Second brand")
    queryset = BrandAdmin(Brand, admin.site).get_queryset(rf.get("/admin/brands/brand/"))

    with django_assert_num_queries(1):
        brands = list(queryset)
        [brand.nomenclature_count for brand in brands]

    assert len(brands) == 2
