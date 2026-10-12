from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("placement_order", "0004_alter_placementorder_managers_placementorder_code1c_and_more")]

    operations = [
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY IF EXISTS "placement_order_code1c_uniq"',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'CREATE UNIQUE INDEX CONCURRENTLY "placement_order_code1c_uniq" ON "placement_order_placementorder" ("code1c")',
            reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS "placement_order_code1c_uniq"',
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY IF EXISTS "placement_order_code1c_like_idx"',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'CREATE INDEX CONCURRENTLY "placement_order_code1c_like_idx" ON "placement_order_placementorder" ("code1c" varchar_pattern_ops)',
            reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS "placement_order_code1c_like_idx"',
        ),
    ]
