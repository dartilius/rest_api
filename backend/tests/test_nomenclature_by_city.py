from datetime import timedelta
from http import HTTPStatus

import pytest
from django.utils import timezone

from addresses.models import (
    Address,
    City,
    Country,
    FederalDistrict,
    LocalityType,
    Region,
    TypeRegion,
)
from counterparties.models import Counterparty
from nomenclatures.models import (
    Nomenclature,
    NomenclatureAddress,
    NomenclatureTenant,
    TypeOfPlace,
)


@pytest.mark.django_db
def test_by_city_uses_main_list_ordering(admin_client, nomenclature, user):
    country = Country.objects.create(name="Тестовая страна")
    district = FederalDistrict.objects.create(
        country=country,
        name="Тестовый округ",
        abbreviated_name="ТО",
    )
    region_type = TypeRegion.objects.create(
        name="Тестовый тип региона",
        abbreviated_name="тест.",
    )
    region = Region.objects.create(
        name="Тестовый регион",
        federal_district=district,
        type_region=region_type,
    )
    locality_type = LocalityType.objects.create(
        name="Тестовый город",
        abbreviated_name="г.",
    )
    city = City.objects.create(
        name="Тестоград",
        region=region,
        locality_type=locality_type,
    )
    address = Address.objects.create(city=city)

    shopping_mall_type = TypeOfPlace.objects.create(name="Торговый центр")
    regular_type = TypeOfPlace.objects.create(name="Магазин")

    nomenclature.typeOfPlace = shopping_mall_type
    nomenclature.for_web = True
    nomenclature.save(update_fields=("typeOfPlace", "for_web"))

    def create_nomenclature(name):
        return Nomenclature.objects.create(
            name=name,
            owner=user,
            settings=nomenclature.settings,
            typeOfPlace=regular_type,
            for_web=True,
        )

    popular = create_nomenclature("Много арендаторов")
    newer = create_nomenclature("Новая")
    older = create_nomenclature("Старая")

    for item in (nomenclature, popular, newer, older):
        NomenclatureAddress.objects.create(
            nomenclature=item,
            address=address,
        )

    tenants = [
        Counterparty.objects.create(owner=user, keyword=f"Арендатор {index}")
        for index in range(2)
    ]
    NomenclatureTenant.objects.bulk_create(
        [
            NomenclatureTenant(nomenclature=popular, tenant=tenant)
            for tenant in tenants
        ]
    )

    now = timezone.now()
    Nomenclature.objects.filter(pk=newer.pk).update(created=now)
    Nomenclature.objects.filter(pk=older.pk).update(created=now - timedelta(days=1))

    response = admin_client.get(f"/api/nomenclatures/by-city/{city.slug}/")

    assert response.status_code == HTTPStatus.OK
    assert response.json()["count"] == 4
    assert [item["id"] for item in response.json()["nomenclatures"]] == [
        str(nomenclature.id),
        str(popular.id),
        str(newer.id),
        str(older.id),
    ]
