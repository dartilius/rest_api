# brands/migrations/0003_initial.py

import re

from django.db import migrations
from transliterate import translit


def refill_slugs(apps, schema_editor):
    Brand = apps.get_model('brands', 'Brand')
    Nomenclature = apps.get_model('nomenclatures', 'Nomenclature')
    db = schema_editor.connection.alias

    queryset = (
        Nomenclature._base_manager
        .filter(
            is_active=True,
            for_web=True,
            typeOfPlace__name="Торговый центр",
        )
    )

    active_brand_ids = set(
        queryset.values_list('brand_id', flat=True).distinct()
    )

    # Сбрасываем slug у неактивных брендов
    Brand.objects.using(db).exclude(
        id__in=active_brand_ids
    ).update(slug=None)

    # Перегенерация slug для активных брендов
    seen = set()

    for brand in Brand.objects.using(db).filter(id__in=active_brand_ids):
        try:
            name_latin = translit(
                brand.name,
                'ru',
                reversed=True
            )
        except Exception:
            name_latin = brand.name

        base = re.sub(
            r'[^\w\s-]',
            '',
            name_latin.lower()
        ).strip()

        base = re.sub(
            r'[\s_-]+',
            '-',
            base
        ) or str(brand.id)[:8]

        slug = base[:90]

        if slug in seen:
            slug = f"{base[:85]}-{str(brand.id)[:8]}"

        seen.add(slug)

        brand.slug = slug
        brand.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('brands', '0002__initial'),
        ('nomenclatures', '__first__'),
    ]

    operations = [
        migrations.RunPython(
            refill_slugs,
            migrations.RunPython.noop
        ),
    ]
