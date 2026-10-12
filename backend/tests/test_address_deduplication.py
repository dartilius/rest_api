from io import StringIO

import pytest
from django.core.management import call_command

from addresses.deduplication import deduplicate_final_addresses, get_or_create_canonical_address
from addresses.models import Address, City, Coordinates, Country, House, LocalityType, Region, Street, StreetType
from counterparties.models import Counterparty
from nomenclatures.models import NomenclatureAddress


def _create_duplicate_addresses() -> tuple[Address, Address]:
    country = Country.objects.create(name="Test country")
    region = Region.objects.create(name="Test region", country=country)
    locality_type = LocalityType.objects.create(name="City", abbreviated_name="city")
    city = City.objects.create(name="Test city", region=region, locality_type=locality_type)
    street_type = StreetType.objects.create(name="Street", abbreviated_name="st")
    street = Street.objects.create(name="Main", city=city, street_type=street_type)
    house = House.objects.create(number="1", street=street)

    common_fields = {
        "country": country,
        "region": region,
        "city": city,
        "street": street,
        "house": house,
    }
    return Address.objects.create(**common_fields), Address.objects.create(**common_fields)


@pytest.mark.django_db
def test_dry_run_does_not_change_duplicate_addresses(nomenclature) -> None:
    original, duplicate = _create_duplicate_addresses()
    NomenclatureAddress.objects.create(nomenclature=nomenclature, address=duplicate)

    results = deduplicate_final_addresses()

    assert len(results) == 1
    assert results[0].applied is False
    assert results[0].nomenclature_links == 1
    assert Address.objects.filter(pk=original.id).exists()
    assert Address.objects.filter(pk=duplicate.id).exists()
    assert NomenclatureAddress.objects.get(nomenclature=nomenclature).address_id == duplicate.id


@pytest.mark.django_db
def test_canonical_creation_reuses_address_when_metadata_changes() -> None:
    original, _duplicate = _create_duplicate_addresses()

    address, created = get_or_create_canonical_address(
        country=original.country,
        region=original.region,
        city=original.city,
        street=original.street,
        house=original.house,
        index="12345",
    )

    assert created is False
    assert address.id in {original.id, _duplicate.id}


@pytest.mark.django_db
def test_equal_coordinate_values_do_not_block_address_deduplication() -> None:
    original, duplicate = _create_duplicate_addresses()
    first_coordinates = Coordinates.objects.create(latitude="55.0000", longitude="92.0000")
    second_coordinates = Coordinates.objects.create(latitude="55.0000", longitude="92.0000")
    Address.objects.filter(pk=original.id).update(coordinates=first_coordinates)
    Address.objects.filter(pk=duplicate.id).update(coordinates=second_coordinates)

    result = deduplicate_final_addresses(apply=True)[0]

    assert result.applied is True
    assert result.metadata_conflicts == ()


@pytest.mark.django_db
def test_apply_moves_all_known_links_before_deleting_duplicate(nomenclature, user) -> None:
    original, duplicate = _create_duplicate_addresses()
    NomenclatureAddress.objects.create(nomenclature=nomenclature, address=duplicate)
    counterparty = Counterparty.objects.create(owner=user, keyword="Address link", address=duplicate)

    results = deduplicate_final_addresses(apply=True)

    assert len(results) == 1
    result = results[0]
    assert result.applied is True
    assert result.nomenclature_links == 1
    assert result.counterparty_links == 1
    assert result.canonical_id == str(duplicate.id)
    assert not Address.objects.filter(pk=original.id).exists()
    assert NomenclatureAddress.objects.get(nomenclature=nomenclature).address_id == duplicate.id
    assert Counterparty.objects.get(pk=counterparty.id).address_id == duplicate.id


@pytest.mark.django_db
def test_conflicting_metadata_is_reported_and_not_deleted() -> None:
    original, duplicate = _create_duplicate_addresses()
    Address.objects.filter(pk=original.id).update(index="12345")
    Address.objects.filter(pk=duplicate.id).update(index="54321")

    output = StringIO()
    call_command("deduplicate_addresses", "--apply", stdout=output)

    assert "SKIPPED: metadata conflicts index" in output.getvalue()
    assert Address.objects.filter(pk=original.id).exists()
    assert Address.objects.filter(pk=duplicate.id).exists()


@pytest.mark.django_db
def test_explicit_conflict_option_keeps_canonical_metadata() -> None:
    original, duplicate = _create_duplicate_addresses()
    Address.objects.filter(pk=original.id).update(index="12345")
    Address.objects.filter(pk=duplicate.id).update(index="54321")

    result = deduplicate_final_addresses(
        apply=True,
        allow_metadata_conflicts=True,
    )[0]

    assert result.applied is True
    assert result.metadata_conflicts == ("index",)
    assert Address.objects.filter(pk__in=[original.id, duplicate.id]).count() == 1
    assert Address.objects.get(pk=result.canonical_id).index in {"12345", "54321"}
