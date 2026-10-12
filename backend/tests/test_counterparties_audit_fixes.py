import pytest
from django.contrib import admin
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIRequestFactory, force_authenticate

from brands.models import Brand
from counterparties.admin import CounterpartiesAdmin
from counterparties.models import Counterparty
from counterparties.views import CounterpartiesViewSet
from promotions.models import Promotion
from promotions.views import PromotionViewSet


@pytest.mark.django_db
def test_create_counterparty_creates_nested_contacts_and_sets_request_owner(user):
    request = APIRequestFactory().post(
        "/api/counterparties/",
        {
            "opf": "FL",
            "first_name": "Иван",
            "last_name": "Петров",
            "contacts": [{"type": "phone", "meaning": "+79990000000"}],
        },
        format="json",
    )
    force_authenticate(request, user=user)

    response = CounterpartiesViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 201
    counterparty = Counterparty.objects.get(pk=response.data["id"])
    assert counterparty.owner == user
    assert list(counterparty.contacts.values_list("meaning", flat=True)) == ["+79990000000"]


@pytest.mark.django_db
def test_employee_can_set_counterparty_service_fields_via_api(admin_user, user):
    request = APIRequestFactory().post(
        "/api/counterparties/",
        {
            "first_name": "From 1C",
            "owner": str(user.id),
            "code1c": "1c-counterparty-code",
            "broadcast": True,
            "is_active": False,
        },
        format="json",
    )
    force_authenticate(request, user=admin_user)

    response = CounterpartiesViewSet.as_view({"post": "create"})(request)

    assert response.status_code == 201
    counterparty = Counterparty.objects.get(pk=response.data["id"])
    assert counterparty.owner == user
    assert counterparty.code1c == "1c-counterparty-code"
    assert counterparty.broadcast is True
    assert counterparty.is_active is False


@pytest.mark.django_db
def test_failed_opf_transition_does_not_modify_counterparty(admin_user):
    counterparty = Counterparty.objects.create(
        opf="OOO",
        keyword="Старое ООО",
        inn="1234567890",
    )
    request = APIRequestFactory().patch(
        f"/api/counterparties/{counterparty.id}/",
        {
            "opf": "FL",
            "first_name": "Иван",
            "last_name": "Петров",
            "inn": "123456789012",
            "address": "00000000-0000-0000-0000-000000000001",
        },
        format="json",
    )
    force_authenticate(request, user=admin_user)

    response = CounterpartiesViewSet.as_view({"patch": "partial_update"})(
        request,
        pk=str(counterparty.id),
    )

    assert response.status_code == 400
    counterparty.refresh_from_db()
    assert counterparty.opf == "OOO"
    assert counterparty.keyword == "Старое ООО"
    assert counterparty.inn == "1234567890"


@pytest.mark.django_db
def test_counterparty_list_uses_prefetched_m2m_relations(admin_user):
    brand = Brand.objects.create(name="List brand")
    first = Counterparty.objects.create(first_name="First")
    second = Counterparty.objects.create(first_name="Second")
    first.brands.add(brand)
    first.contact_persons.add(admin_user)
    second.brands.add(brand)
    second.contact_persons.add(admin_user)

    request = APIRequestFactory().get("/api/counterparties/")
    force_authenticate(request, user=admin_user)
    with CaptureQueriesContext(connection) as queries:
        response = CounterpartiesViewSet.as_view({"get": "list"})(request)

    relation_queries = [
        query["sql"]
        for query in queries.captured_queries
        if '"counterparties_brands"' in query["sql"] or '"counterparties_contact_persons"' in query["sql"]
    ]
    assert response.status_code == 200
    assert len(relation_queries) == 2


@pytest.mark.django_db
def test_counterparty_admin_uses_annotated_query_and_prefetched_brands(rf, django_assert_num_queries):
    brand = Brand.objects.create(name="Admin brand")
    counterparty = Counterparty.objects.create(first_name="Admin")
    counterparty.brands.add(brand)
    queryset = CounterpartiesAdmin(Counterparty, admin.site).get_queryset(
        rf.get("/admin/counterparties/counterparty/"),
    )

    with django_assert_num_queries(2):
        counterparties = list(queryset)
        [counterparty.name for counterparty in counterparties]

    assert counterparties[0].brands_count == 1


@pytest.mark.django_db
def test_contact_person_can_list_own_promotions(user):
    user.role = "broadcast"
    user.save(update_fields=["role"])
    counterparty = Counterparty.objects.create(first_name="Promotion owner")
    counterparty.contact_persons.add(user)
    promotion = Promotion.objects.create(name="Promotion", counterparty=counterparty)
    request = APIRequestFactory().get("/api/promotions/")
    force_authenticate(request, user=user)

    response = PromotionViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert response.data["results"][0]["id"] == str(promotion.id)
