from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("nomenclatures", "0012_nomenclature_broadcast"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="nomenclature",
            index=models.Index(
                fields=["-created", "id"],
                name="nom_web_active_created_idx",
                condition=models.Q(for_web=True, is_active=True),
            ),
        ),
        AddIndexConcurrently(
            model_name="nomenclature",
            index=models.Index(
                fields=["brand", "pricePerMonth"],
                name="nom_web_brand_price_idx",
                condition=models.Q(for_web=True, is_active=True),
            ),
        ),
        AddIndexConcurrently(
            model_name="nomenclature",
            index=GinIndex(
                fields=["search_vector"],
                name="nom_search_vector_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        AddIndexConcurrently(
            model_name="nomenclatureimage",
            index=models.Index(
                fields=["nomenclature", "type", "-created", "id"],
                name="nom_image_type_created_idx",
            ),
        ),
    ]
