from io import StringIO

import pytest
from django.core.management import call_command

from nomenclatures.models import Nomenclature


@pytest.mark.django_db
def test_generate_catalog_slugs_resolves_duplicate_slugs(
    nomenclature,
    nomenclature_1,
    user,
):
    slug = "duplicate-legacy-slug"
    occupied_slug = f"{slug}_2"
    Nomenclature.objects.filter(pk__in=[nomenclature.pk, nomenclature_1.pk]).update(
        old_catalog_slug=slug,
    )
    Nomenclature.objects.create(
        name="Occupied suffix",
        owner=user,
        timezone="Etc/GMT-7",
        settings=nomenclature.settings,
        old_catalog_slug=occupied_slug,
    )

    call_command("generate_catalog_slugs", stdout=StringIO())

    assert Nomenclature.objects.filter(old_catalog_slug=slug).count() == 1
    assert Nomenclature.objects.filter(old_catalog_slug=occupied_slug).exists()
    assert Nomenclature.objects.filter(old_catalog_slug=f"{slug}_3").count() == 1


@pytest.mark.django_db
def test_save_adds_suffix_to_duplicate_legacy_slug(nomenclature, user):
    slug = "duplicate-legacy-slug"
    Nomenclature.objects.filter(pk=nomenclature.pk).update(old_catalog_slug=slug)

    duplicate = Nomenclature.objects.create(
        name="Duplicate slug",
        owner=user,
        timezone="Etc/GMT-7",
        settings=nomenclature.settings,
        old_catalog_slug=slug,
    )

    assert duplicate.old_catalog_slug == f"{slug}_2"


@pytest.mark.django_db
def test_web_detail_allows_nomenclature_primary_key(anon_client, nomenclature):
    slug = "web-legacy-slug"
    Nomenclature.objects.filter(pk=nomenclature.pk).update(
        old_catalog_slug=slug,
        for_web=True,
    )

    response = anon_client.get(f"/api/nomenclatures/web/{nomenclature.id}/")

    assert response.status_code == 200
    assert response.json()["id"] == str(nomenclature.id)
