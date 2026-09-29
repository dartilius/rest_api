"""Safe detection and consolidation of structurally duplicate addresses."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.db.models import Count

from counterparties.models import Counterparty
from nomenclatures.models import NomenclatureAddress

from .models import Address


ADDRESS_IDENTITY_FIELDS = (
    "country_id",
    "federal_district_id",
    "region_id",
    "city_id",
    "administrative_territory_id",
    "administrative_unit_id",
    "street_id",
    "house_id",
    "building_id",
)

_METADATA_FIELDS = (
    "coordinates_id",
    "microdistrict",
    "index",
    "latitude",
    "longitude",
)


@dataclass(frozen=True)
class DuplicateAddressResult:
    """Result for one structural address group."""

    canonical_id: str
    duplicate_ids: tuple[str, ...]
    nomenclature_links: int
    counterparty_links: int
    metadata_conflicts: tuple[str, ...]
    applied: bool


def _is_missing(value: Any) -> bool:
    return value is None or value == ""


def get_or_create_canonical_address(**address_fields: Any) -> tuple[Address, bool]:
    """Return the existing physical address or create it after hierarchy checks."""
    candidate = Address(**address_fields)
    candidate.full_clean()
    identity = {
        field_name: getattr(candidate, field_name)
        for field_name in ADDRESS_IDENTITY_FIELDS
    }
    existing = Address.objects.filter(**identity).order_by("id").first()
    if existing:
        return existing, False

    candidate.save()
    return candidate, True


def _identity_groups() -> list[dict[str, Any]]:
    return list(
        Address.objects.values(*ADDRESS_IDENTITY_FIELDS)
        .annotate(address_count=Count("id"))
        .filter(address_count__gt=1)
        .order_by(*ADDRESS_IDENTITY_FIELDS)
    )


def _link_counts(address_ids: list[Any]) -> tuple[Counter, Counter]:
    nomenclature_counts = Counter(
        NomenclatureAddress.objects.filter(address_id__in=address_ids).values_list(
            "address_id", flat=True
        )
    )
    counterparty_counts = Counter(
        Counterparty.objects.filter(address_id__in=address_ids).values_list(
            "address_id", flat=True
        )
    )
    return nomenclature_counts, counterparty_counts


def _choose_canonical(
    addresses: list[Address], nomenclature_counts: Counter, counterparty_counts: Counter
) -> Address:
    """Keep the most referenced address; UUID gives a deterministic tie-break."""
    return min(
        addresses,
        key=lambda address: (
            -(nomenclature_counts[address.id] + counterparty_counts[address.id]),
            str(address.id),
        ),
    )


def _metadata_plan(addresses: list[Address], canonical: Address) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Fill absent canonical metadata only when all non-empty values agree."""
    updates: dict[str, Any] = {}
    conflicts: list[str] = []

    for field_name in _METADATA_FIELDS:
        values = {
            getattr(address, field_name)
            for address in addresses
            if not _is_missing(getattr(address, field_name))
        }
        if len(values) > 1:
            conflicts.append(field_name)
            continue
        if values and _is_missing(getattr(canonical, field_name)):
            updates[field_name] = values.pop()

    return updates, tuple(conflicts)


def deduplicate_final_addresses(
    *, apply: bool = False, allow_metadata_conflicts: bool = False
) -> list[DuplicateAddressResult]:
    """Report or merge exact final-address duplicates without losing references.

    ``apply=False`` is read-only. With ``apply=True`` every group is handled in
    its own transaction: links are moved first and rows are removed only after
    no link still points to a duplicate. Metadata conflicts are skipped unless
    ``allow_metadata_conflicts`` explicitly keeps the canonical value.
    """
    results: list[DuplicateAddressResult] = []

    for identity in _identity_groups():
        identity.pop("address_count")
        queryset = Address.objects.filter(**identity).order_by("id")

        if not apply:
            addresses = list(queryset)
            if len(addresses) < 2:
                continue

            address_ids = [address.id for address in addresses]
            nomenclature_counts, counterparty_counts = _link_counts(address_ids)
            canonical = _choose_canonical(addresses, nomenclature_counts, counterparty_counts)
            duplicate_ids = [address.id for address in addresses if address.id != canonical.id]
            metadata_updates, metadata_conflicts = _metadata_plan(addresses, canonical)
            results.append(
                DuplicateAddressResult(
                    canonical_id=str(canonical.id),
                    duplicate_ids=tuple(str(address_id) for address_id in duplicate_ids),
                    nomenclature_links=sum(nomenclature_counts.values()),
                    counterparty_links=sum(counterparty_counts.values()),
                    metadata_conflicts=metadata_conflicts,
                    applied=False,
                )
            )
            continue

        with transaction.atomic():
            addresses = list(queryset.select_for_update())
            if len(addresses) < 2:
                continue

            address_ids = [address.id for address in addresses]
            nomenclature_counts, counterparty_counts = _link_counts(address_ids)
            canonical = _choose_canonical(addresses, nomenclature_counts, counterparty_counts)
            duplicate_ids = [address.id for address in addresses if address.id != canonical.id]
            metadata_updates, metadata_conflicts = _metadata_plan(addresses, canonical)
            can_apply = not metadata_conflicts or allow_metadata_conflicts

            if can_apply:
                if metadata_updates:
                    Address.objects.filter(pk=canonical.id).update(**metadata_updates)

                NomenclatureAddress.objects.filter(address_id__in=duplicate_ids).update(
                    address_id=canonical.id
                )
                Counterparty.objects.filter(address_id__in=duplicate_ids).update(
                    address_id=canonical.id
                )

                if NomenclatureAddress.objects.filter(address_id__in=duplicate_ids).exists():
                    raise RuntimeError("Не удалось перенести ссылки номенклатур на канонический адрес")
                if Counterparty.objects.filter(address_id__in=duplicate_ids).exists():
                    raise RuntimeError("Не удалось перенести ссылки контрагентов на канонический адрес")

                Address.objects.filter(pk__in=duplicate_ids).delete()

            results.append(
                DuplicateAddressResult(
                    canonical_id=str(canonical.id),
                    duplicate_ids=tuple(str(address_id) for address_id in duplicate_ids),
                    nomenclature_links=sum(nomenclature_counts.values()),
                    counterparty_links=sum(counterparty_counts.values()),
                    metadata_conflicts=metadata_conflicts,
                    applied=can_apply,
                )
            )

    return results


def address_metadata_conflicts() -> list[dict[str, Any]]:
    """Return read-only details for groups blocked by conflicting metadata."""
    conflicts: list[dict[str, Any]] = []
    for identity in _identity_groups():
        identity.pop("address_count")
        addresses = list(Address.objects.filter(**identity).order_by("id"))
        address_ids = [address.id for address in addresses]
        nomenclature_counts, counterparty_counts = _link_counts(address_ids)
        canonical = _choose_canonical(addresses, nomenclature_counts, counterparty_counts)
        _updates, fields = _metadata_plan(addresses, canonical)
        if not fields:
            continue

        values = {
            field_name: [
                {"address_id": str(address.id), "value": str(getattr(address, field_name) or "")}
                for address in addresses
            ]
            for field_name in fields
        }
        conflicts.append(
            {
                "canonical_id": str(canonical.id),
                "address_ids": [str(address_id) for address_id in address_ids],
                "conflict_fields": list(fields),
                "values": values,
                "nomenclature_links": sum(nomenclature_counts.values()),
                "counterparty_links": sum(counterparty_counts.values()),
            }
        )
    return conflicts
