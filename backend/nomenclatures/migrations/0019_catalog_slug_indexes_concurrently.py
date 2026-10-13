from django.db import migrations


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("nomenclatures", "0018_reconcile_catalog_storage")]

    operations = [
        # Match Django's implicit names; rebuild invalid interrupted indexes too.
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY IF EXISTS "nomenclature_old_catalog_slug_81f6849d"',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'CREATE INDEX CONCURRENTLY "nomenclature_old_catalog_slug_81f6849d" '
            'ON "nomenclature" ("old_catalog_slug")',
            # May already have existed before reconciliation; retain on rollback.
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY IF EXISTS "nomenclature_old_catalog_slug_81f6849d_like"',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'CREATE INDEX CONCURRENTLY "nomenclature_old_catalog_slug_81f6849d_like" '
            'ON "nomenclature" ("old_catalog_slug" varchar_pattern_ops)',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
