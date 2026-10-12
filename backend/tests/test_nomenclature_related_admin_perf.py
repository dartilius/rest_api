from decimal import Decimal

import pytest
from django.contrib.admin.sites import site
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from brands.models import Brand
from counterparties.models import Counterparty
from nomenclatures.admin import DiscountStationFilter
from nomenclatures.models import (
    DiscountRule,
    NomenclatureAvailability,
    NomenclatureImage,
    NomenclatureTenant,
    NomenclatureVideo,
    StatusHistory,
)


@pytest.mark.django_db
def test_tenant_list_labels_prefetch_counterparty_brands(
    nomenclature, nomenclature_1, user, super_user
):
    brand = Brand.objects.create(name="Tenant brand")
    for station in (nomenclature, nomenclature_1):
        tenant = Counterparty.objects.create(owner=user, keyword="Tenant")
        tenant.brands.add(brand)
        NomenclatureTenant.objects.create(nomenclature=station, tenant=tenant)
    request = RequestFactory().get("/admin/nomenclatures/nomenclaturetenant/")
    request.user = super_user
    model_admin = site._registry[NomenclatureTenant]

    with CaptureQueriesContext(connection) as queries:
        rows = list(model_admin.get_queryset(request))
        labels = [str(row.tenant) for row in rows]
        names = [model_admin.nomenclature_name(row) for row in rows]

    assert len(queries) == 2
    assert labels == ["Tenant (Tenant brand)", "Tenant (Tenant brand)"]
    assert set(names) == {nomenclature.name, nomenclature_1.name}


@pytest.mark.django_db
def test_discount_station_filter_uses_uuid_and_rejects_invalid_input(
    nomenclature, nomenclature_1, super_user
):
    for station in (nomenclature, nomenclature_1):
        DiscountRule.objects.create(
            nomenclature=station, days_from=1, coefficient=Decimal("0.900")
        )
    model_admin = site._registry[DiscountRule]
    request = RequestFactory().get("/admin/", {"station_uuid": str(nomenclature.pk)})
    request.user = super_user
    with CaptureQueriesContext(connection) as queries:
        station_filter = DiscountStationFilter(
            request, {"station_uuid": [str(nomenclature.pk)]}, DiscountRule, model_admin
        )
    assert len(queries) == 0  # Building the filter must not enumerate the station catalog.
    assert list(
        station_filter.queryset(request, DiscountRule.objects.all()).values_list(
            "nomenclature_id", flat=True
        )
    ) == [nomenclature.pk]

    invalid_filter = DiscountStationFilter(
        request, {"station_uuid": ["invalid"]}, DiscountRule, model_admin
    )
    assert not invalid_filter.queryset(request, DiscountRule.objects.all()).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("model", [NomenclatureImage, NomenclatureVideo])
def test_media_admin_loads_file_fields_without_deferred_queries(
    model, nomenclature, super_user
):
    # bulk_create avoids writing a file to the external object storage.
    model.objects.bulk_create([
        model(nomenclature=nomenclature, source="sample.png", type="interior", hash="a" * 64),
        model(nomenclature=nomenclature, source="sample2.png", type="exterior", hash="b" * 64),
    ])
    request = RequestFactory().get("/admin/")
    request.user = super_user
    model_admin = site._registry[model]

    with CaptureQueriesContext(connection) as queries:
        rows = list(model_admin.get_queryset(request))
        files = {row.source.name for row in rows}
        labels = [str(row) for row in rows]

    assert len(queries) == 1
    assert files == {"sample.png", "sample2.png"}
    assert all(nomenclature.name in label for label in labels)


@pytest.mark.django_db
@pytest.mark.parametrize("model", [NomenclatureAvailability, StatusHistory, DiscountRule])
def test_related_admin_rows_render_without_per_row_queries(
    model, nomenclature, nomenclature_1, super_user
):
    for station in (nomenclature, nomenclature_1):
        if model is DiscountRule:
            model.objects.create(nomenclature=station, days_from=1, coefficient=Decimal("0.900"))
        elif model is NomenclatureAvailability:
            model.objects.create(client=station, status=0, last_answer_date=timezone.now())
        else:
            model.objects.create(client=station, status=0)
    request = RequestFactory().get("/admin/")
    request.user = super_user
    model_admin = site._registry[model]

    with CaptureQueriesContext(connection) as queries:
        rows = list(model_admin.get_queryset(request))
        names = [
            model_admin.nomenclature_name(row) if model is DiscountRule else model_admin.client_name(row)
            for row in rows
        ]
        if model is DiscountRule:
            assert all("10.0%" in model_admin.discount_percent(row) for row in rows)
        else:
            assert all("Online" in model_admin.status_display(row) for row in rows)

    assert len(queries) == 1
    assert set(names) == {nomenclature.name, nomenclature_1.name}
@pytest.mark.django_db
@pytest.mark.parametrize("model_name", [
    "nomenclature", "nomenclaturetenant", "typeofplace", "nomenclatureavailability",
    "statushistory", "nomenclatureimage", "nomenclaturevideo", "nomenclatureaddress",
    "discountrule", "stationcredential", "stationinstallation", "stationcommandv2",
])
def test_nomenclature_admin_changelists_open(client, super_user, model_name):
    from django.urls import reverse

    client.force_login(super_user)
    response = client.get(reverse(f"admin:nomenclatures_{model_name}_changelist"))
    assert response.status_code == 200
