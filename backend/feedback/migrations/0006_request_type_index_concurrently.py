from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("feedback", "0005_feedback_company_feedback_consent_and_more")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # An interrupted concurrent build can leave an invalid index.
                migrations.RunSQL(
                    'DROP INDEX CONCURRENTLY IF EXISTS "feedback_request_type_idx"',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    'CREATE INDEX CONCURRENTLY "feedback_request_type_idx" ON "feedback" ("request_type")',
                    reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS "feedback_request_type_idx"',
                ),
                migrations.RunSQL(
                    'DROP INDEX CONCURRENTLY IF EXISTS "feedback_request_type_like_idx"',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    'CREATE INDEX CONCURRENTLY "feedback_request_type_like_idx" ON "feedback" ("request_type" varchar_pattern_ops)',
                    reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS "feedback_request_type_like_idx"',
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="feedback",
                    name="request_type",
                    field=models.CharField(
                        max_length=32,
                        choices=[("general", "Общее обращение"), ("corporate_broadcast", "Корпоративное вещание")],
                        default="general", db_default="general", db_index=True,
                    ),
                ),
            ],
        ),
    ]
