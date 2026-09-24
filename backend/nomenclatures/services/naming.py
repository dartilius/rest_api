"""Naming helpers shared by independent nomenclature API contracts."""

from django.core.exceptions import ObjectDoesNotExist


def build_nomenclature_web_name(nomenclature):
    """Build the public nomenclature name from its place, brand and address."""
    title_parts = []
    if nomenclature.typeOfPlace and nomenclature.typeOfPlace.abbreviation:
        title_parts.append(nomenclature.typeOfPlace.abbreviation)
    if nomenclature.brand and nomenclature.brand.name:
        title_parts.append(nomenclature.brand.name)

    address_parts = []
    try:
        address = nomenclature.address.address
    except ObjectDoesNotExist:
        address = None

    if address:
        if address.city and address.city.name:
            address_parts.append(f"г. {address.city.name}")
        if address.street and address.street.name:
            address_parts.append(f"ул. {address.street.name}")

        house_number = None
        if address.house and address.house.number:
            house_number = address.house.number
        elif address.building and address.building.number:
            house_number = address.building.number
        if house_number:
            address_parts.append(house_number)

    generated_parts = []
    if title_parts:
        generated_parts.append(" ".join(title_parts))
    generated_parts.extend(address_parts)
    return ", ".join(generated_parts) or nomenclature.name
