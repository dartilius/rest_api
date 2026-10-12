from django.db import migrations, models


class AtomicDatabaseAndState(migrations.SeparateDatabaseAndState):
    """Keep SET LOCAL and short DDL in one transaction, even on rollback."""

    atomic = True


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("placement_order", "0005_code1c_indexes_concurrently")]

    operations = [
        # DROP CONSTRAINT also drops its owned index. Restore the 0005 schema
        # on reversal outside a transaction so 0006 can be applied again.
        migrations.RunSQL(
            migrations.RunSQL.noop,
            reverse_sql=[
                'DROP INDEX CONCURRENTLY IF EXISTS "placement_order_code1c_uniq"',
                'CREATE UNIQUE INDEX CONCURRENTLY "placement_order_code1c_uniq" '
                'ON "placement_order_placementorder" ("code1c")',
            ],
        ),
        AtomicDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    "SET LOCAL lock_timeout = '2s';\n"
                    'ALTER TABLE "placement_order_placementorder" ADD CONSTRAINT '
                    '"placement_order_code1c_uniq" UNIQUE USING INDEX "placement_order_code1c_uniq"',
                    reverse_sql="SET LOCAL lock_timeout = '2s';\n"
                    'ALTER TABLE "placement_order_placementorder" DROP CONSTRAINT IF EXISTS "placement_order_code1c_uniq"',
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="placementorder", name="code1c",
                    field=models.CharField(blank=True, null=True, unique=True),
                ),
            ],
        ),
    ]
