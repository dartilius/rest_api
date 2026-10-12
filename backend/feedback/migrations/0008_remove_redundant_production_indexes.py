"""Production 0005 created implicit indexes; 0006 supplies their replacements."""

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("feedback", "0007_reconcile_production_db_defaults")]

    operations = [
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY IF EXISTS "feedback_request_type_ee432142"',
            # 0006's equivalent indexes remain; a redundant copy is unnecessary.
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP INDEX CONCURRENTLY IF EXISTS "feedback_request_type_ee432142_like"',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
