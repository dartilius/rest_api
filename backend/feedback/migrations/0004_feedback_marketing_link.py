# Generated manually for the marketing funnel contract.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("placement_order", "0002_placementorder_marketing_funnel"),
        ("feedback", "0003_feedback_brand_id_feedback_nomenclatures_ids_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="feedback",
            name="attribution",
            field=models.JSONField(blank=True, null=True, verbose_name="Marketing attribution"),
        ),
        migrations.AddField(
            model_name="feedback",
            name="placement_order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="feedback_requests",
                to="placement_order.placementorder",
                verbose_name="Placement order",
            ),
        ),
    ]
