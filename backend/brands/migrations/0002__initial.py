# brands/migrations/0002_brand_slug.py
import re
from django.db import migrations, models
from transliterate import translit


def fill_slugs(apps, schema_editor):
    Brand = apps.get_model('brands', 'Brand')
    seen = set()
    for brand in Brand.objects.using(schema_editor.connection.alias).all():
        try:
            name_latin = translit(brand.name, 'ru', reversed=True)
        except Exception:
            name_latin = brand.name

        base = re.sub(r'[^\w\s-]', '', name_latin.lower()).strip()
        base = re.sub(r'[\s_-]+', '-', base) or str(brand.id)[:8]
        slug = base[:90]

        if slug in seen or not slug:
            slug = f"{base[:85]}-{str(brand.id)[:8]}"

        seen.add(slug)
        brand.slug = slug
        brand.save(update_fields=['slug'])


class Migration(migrations.Migration):
    dependencies = [
        ('brands', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='brand',
            name='slug',
            field=models.SlugField(
                blank=True, max_length=100, null=True,
                unique=True, verbose_name='Slug'
            ),
        ),
        migrations.RunPython(fill_slugs, migrations.RunPython.noop),
    ]
