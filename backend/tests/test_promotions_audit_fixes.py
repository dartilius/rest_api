from datetime import date

import pytest
from django.contrib import admin
from rest_framework.test import APIRequestFactory, force_authenticate

from brands.models import Brand
from counterparties.models import Counterparty
from promotions.admin import PromotionAdmin
from promotions.models import Promotion
from promotions.views import PromotionViewSet


@pytest.mark.django_db
def test_ordinary_user_cannot_retrieve_another_promotion(user):
    promotion = Promotion.objects.create(name="Private promotion")
    request = APIRequestFactory().get(f"/api/promotions/{promotion.id}/")
    force_authenticate(request, user=user)

    response = PromotionViewSet.as_view({"get": "retrieve"})(
        request,
        id_or_code1c=str(promotion.id),
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_contact_person_cannot_move_promotion_to_another_counterparty(user):
    user.role = "ad"
    user.save(update_fields=["role"])
    own_counterparty = Counterparty.objects.create(first_name="Own")
    other_counterparty = Counterparty.objects.create(first_name="Other")
    own_counterparty.contact_persons.add(user)
    promotion = Promotion.objects.create(name="Promotion", counterparty=own_counterparty)
    request = APIRequestFactory().patch(
        f"/api/promotions/{promotion.id}/",
        {"counterparty": str(other_counterparty.id)},
        format="json",
    )
    force_authenticate(request, user=user)

    response = PromotionViewSet.as_view({"patch": "partial_update"})(
        request,
        id_or_code1c=str(promotion.id),
    )

    assert response.status_code == 403
    promotion.refresh_from_db()
    assert promotion.counterparty == own_counterparty


@pytest.mark.django_db
def test_promotion_detail_with_counterparty_and_brands_is_serialized(admin_user, django_assert_num_queries):
    brand = Brand.objects.create(name="Promotion brand")
    counterparty = Counterparty.objects.create(first_name="Counterparty")
    counterparty.brands.add(brand)
    promotion = Promotion.objects.create(name="Promotion", counterparty=counterparty)
    request = APIRequestFactory().get(f"/api/promotions/{promotion.id}/")
    force_authenticate(request, user=admin_user)

    with django_assert_num_queries(2):
        response = PromotionViewSet.as_view({"get": "retrieve"})(
            request,
            id_or_code1c=str(promotion.id),
        )

    assert response.status_code == 200
    assert response.data["counterparty"]["brands"] == [
        {"id": str(brand.id), "name": "Promotion brand", "description": None},
    ]


@pytest.mark.django_db
def test_promotion_list_prefetches_counterparty_brands(admin_user, django_assert_num_queries):
    brand = Brand.objects.create(name="Promotion brand")
    counterparty = Counterparty.objects.create(first_name="Counterparty")
    counterparty.brands.add(brand)
    Promotion.objects.create(name="Promotion 1", counterparty=counterparty)
    Promotion.objects.create(name="Promotion 2", counterparty=counterparty)
    request = APIRequestFactory().get("/api/promotions/")
    force_authenticate(request, user=admin_user)

    with django_assert_num_queries(3):
        response = PromotionViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
def test_promotion_admin_prefetches_counterparty_brands(rf, django_assert_num_queries):
    brand = Brand.objects.create(name="Admin promotion brand")
    counterparty = Counterparty.objects.create(first_name="Admin counterparty")
    counterparty.brands.add(brand)
    Promotion.objects.create(name="Admin promotion 1", counterparty=counterparty)
    Promotion.objects.create(name="Admin promotion 2", counterparty=counterparty)
    queryset = PromotionAdmin(Promotion, admin.site).get_queryset(
        rf.get("/admin/promotions/promotion/"),
    )

    with django_assert_num_queries(2):
        promotions = list(queryset)
        [str(promotion.counterparty) for promotion in promotions]

    assert len(promotions) == 2


@pytest.mark.django_db
def test_promotion_rejects_reversed_periods(admin_user):
    request = APIRequestFactory().post(
        "/api/promotions/",
        {
            "name": "Invalid dates",
            "start_period": date(2026, 9, 2),
            "end_period": date(2026, 9, 1),
        },
        format="json",
    )
    force_authenticate(request, user=admin_user)

    response = PromotionViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 400
    assert "end_period" in response.data
