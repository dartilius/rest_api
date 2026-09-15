# Generated manually for the marketing funnel contract.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("placement_order", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="placementorder",
            name="attribution",
            field=models.JSONField(blank=True, null=True, verbose_name="Marketing attribution"),
        ),
        migrations.AddField(
            model_name="placementorder",
            name="booked_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="placementorder",
            name="commercial_status",
            field=models.CharField(
                choices=[
                    ("new", "New"),
                    ("qualified", "Qualified"),
                    ("proposal_sent", "Proposal sent"),
                    ("booked", "Booked"),
                    ("lost", "Lost"),
                ],
                db_index=True,
                default="new",
                max_length=16,
                verbose_name="Commercial status",
            ),
        ),
        migrations.AddField(
            model_name="placementorder",
            name="lost_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="placementorder",
            name="lost_reason",
            field=models.CharField(
                blank=True,
                choices=[
                    ("no_contact", "No contact"),
                    ("budget", "Budget"),
                    ("timing", "Timing"),
                    ("inventory", "Inventory"),
                    ("competitor", "Competitor"),
                    ("other", "Other"),
                ],
                max_length=16,
                null=True,
                verbose_name="Lost reason",
            ),
        ),
        migrations.AddField(
            model_name="placementorder",
            name="proposal_sent_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="placementorder",
            name="qualified_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
