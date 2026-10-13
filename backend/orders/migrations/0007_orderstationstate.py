import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0006_order_start_to_close_policy")]

    operations = [
        migrations.RunSQL("SET LOCAL lock_timeout = '2s'", reverse_sql=migrations.RunSQL.noop),
        migrations.CreateModel(
            name="OrderStationState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("desired_action", models.CharField(choices=[("apply", "Apply"), ("cancel", "Cancel")], default="apply", max_length=8)),
                ("desired_revision", models.PositiveIntegerField(default=1)),
                ("status", models.CharField(choices=[("queued", "Queued"), ("delivered", "Delivered"), ("received", "Received"), ("downloading", "Downloading"), ("ready", "Ready"), ("applied", "Applied"), ("cancelled", "Cancelled"), ("failed", "Failed"), ("superseded", "Superseded")], default="queued", max_length=16)),
                ("command_id", models.UUIDField(blank=True, null=True, unique=True)),
                ("received_revision", models.PositiveIntegerField(blank=True, null=True)),
                ("ready_revision", models.PositiveIntegerField(blank=True, null=True)),
                ("applied_revision", models.PositiveIntegerField(blank=True, null=True)),
                ("on_air_revision", models.PositiveIntegerField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("nomenclature", models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name="order_delivery_states", to="nomenclatures.nomenclature")),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="station_state", to="orders.order")),
            ],
            options={"db_table": "order_station_state"},
        ),
        migrations.AddIndex(model_name="orderstationstate", index=models.Index(fields=["nomenclature", "status"], name="order_station_state_ns_idx")),
    ]
