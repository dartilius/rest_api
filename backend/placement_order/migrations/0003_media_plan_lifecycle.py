from django.db import migrations, models
from django.utils import timezone


def populate_media_plan_fields(apps, schema_editor):
    PlacementOrder = apps.get_model("placement_order", "PlacementOrder")
    used_names = set()
    for order in PlacementOrder.objects.order_by("created", "id").iterator():
        day = order.created.date() if order.created else timezone.localdate()
        base_name = f"Медиаплан {day:%Y-%m-%d}"
        name = base_name
        suffix = 2
        while name in used_names:
            name = f"{base_name} {suffix}"
            suffix += 1
        used_names.add(name)
        order.name = name
        order.plan_number = f"MP-{day:%Y%m%d}-{str(order.id).replace('-', '')[:8].upper()}"
        order.revision = 1
        order.save(update_fields=["name", "plan_number", "revision"])


class Migration(migrations.Migration):
    dependencies = [("placement_order", "0002_placementorder_marketing_funnel")]

    operations = [
        migrations.AddField(
            model_name="placementorder",
            name="name",
            field=models.CharField(blank=True, default="", max_length=120, verbose_name="Название медиаплана"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="placementorder",
            name="plan_number",
            field=models.CharField(blank=True, max_length=24, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="placementorder",
            name="revision",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="placementorder",
            name="manager_comment",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="placementorder",
            name="updated",
            field=models.DateTimeField(default=timezone.now),
        ),
        migrations.RunPython(populate_media_plan_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="placementorder",
            name="updated",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="placementorder",
            name="commercial_status",
            field=models.CharField(
                choices=[
                    ("new", "Новый"),
                    ("qualified", "Квалифицирован"),
                    ("proposal_sent", "Предложение отправлено"),
                    ("booked", "Забронирован"),
                    ("lost", "Проигран"),
                ],
                db_index=True,
                default="new",
                max_length=16,
                verbose_name="Commercial status",
            ),
        ),
    ]
