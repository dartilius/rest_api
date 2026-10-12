import re

import pytest
from django.contrib.admin.sites import site
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from addresses.models import Address, City, Country, House, LocalityType, Region, Street, StreetType
from nomenclatures.admin import NomenclatureAddressAdmin
from nomenclatures.models import NomenclatureAddress


@pytest.mark.django_db
def test_address_admin_list_renders_addresses_without_per_row_queries(
    nomenclature, nomenclature_1, super_user
) -> None:
    country = Country.objects.create(name="Test country")
    region = Region.objects.create(name="Test region", country=country)
    locality_type = LocalityType.objects.create(name="City", abbreviated_name="city")
    city = City.objects.create(name="Test city", region=region, locality_type=locality_type)
    street_type = StreetType.objects.create(name="Street", abbreviated_name="st")
    street = Street.objects.create(name="Main", city=city, street_type=street_type)
    house = House.objects.create(number="1", street=street)
    address = Address.objects.create(
        country=country, region=region, city=city, street=street, house=house
    )
    NomenclatureAddress.objects.create(nomenclature=nomenclature, address=address)
    NomenclatureAddress.objects.create(nomenclature=nomenclature_1, address=address)

    request = RequestFactory().get("/admin/nomenclatures/nomenclatureaddress/")
    request.user = super_user
    model_admin = site._registry[NomenclatureAddress]
    assert isinstance(model_admin, NomenclatureAddressAdmin)

    with CaptureQueriesContext(connection) as queries:
        rows = list(model_admin.get_queryset(request).order_by("nomenclature__name"))
        rendered = [model_admin.address_short(row) for row in rows]

    assert len(rows) == 2
    assert all("Test city" in value and "Main" in value for value in rendered)
    assert len(queries) == 1


@pytest.mark.django_db
def test_address_admin_change_form_uses_lazy_related_widgets(
    client, super_user, nomenclature
) -> None:
    NomenclatureAddress.objects.create(nomenclature=nomenclature)
    client.force_login(super_user)

    response = client.get(
        reverse("admin:nomenclatures_nomenclatureaddress_change", args=[nomenclature.pk])
    )

    assert response.status_code == 200
    assert b"admin-autocomplete" in response.content
    selected_option = re.search(
        rf'<option value="{nomenclature.pk}" selected>([^<]+)</option>',
        response.content.decode(),
    )
    assert selected_option is not None
    assert selected_option.group(1) == nomenclature.name

    response = client.post(
        reverse("admin:nomenclatures_nomenclatureaddress_change", args=[nomenclature.pk]),
        {"nomenclature": str(nomenclature.pk), "address": ""},
    )
    assert response.status_code == 302
    assert NomenclatureAddress.objects.filter(nomenclature=nomenclature).exists()
