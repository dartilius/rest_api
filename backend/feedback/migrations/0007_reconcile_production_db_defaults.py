"""Applied production 0005 predates the database defaults in repository 0005.

Update the existing columns explicitly; editing an already applied migration
cannot update database storage. Existing values are not changed.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("feedback", "0006_request_type_index_concurrently")]

    operations = [
        migrations.RunSQL(
            """
            SET LOCAL lock_timeout = '2s';
            ALTER TABLE "feedback" ALTER COLUMN "company" SET DEFAULT '';
            ALTER TABLE "feedback" ALTER COLUMN "consent" SET DEFAULT false;
            ALTER TABLE "feedback" ALTER COLUMN "consent_version" SET DEFAULT '';
            ALTER TABLE "feedback" ALTER COLUMN "request_data" SET DEFAULT '{}'::jsonb;
            ALTER TABLE "feedback" ALTER COLUMN "request_type" SET DEFAULT 'general';
            """,
            # Defaults also support old workers; retain them on code rollback.
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
