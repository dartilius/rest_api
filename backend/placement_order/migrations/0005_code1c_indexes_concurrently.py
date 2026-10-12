from django.db import migrations, router


def has_unique_code1c(schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_constraint c
                JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attname = 'code1c'
                JOIN pg_index i ON i.indexrelid = c.conindid
                WHERE c.conrelid = to_regclass('placement_order_placementorder')
                  AND c.contype = 'u' AND c.conkey = ARRAY[a.attnum]
                  AND i.indisvalid AND i.indisunique
            )
        """)
        return cursor.fetchone()[0]


class RunSQLUnlessCode1cUnique(migrations.RunSQL):
    """Reuse a production constraint; otherwise build the new indexes."""

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if not router.allow_migrate(schema_editor.connection.alias, app_label, **self.hints):
            return
        if schema_editor.collect_sql:
            schema_editor.collected_sql.append("-- Conditional SQL: execute only if no valid UNIQUE(code1c) constraint exists.")
            return super().database_forwards(app_label, schema_editor, from_state, to_state)
        if not has_unique_code1c(schema_editor):
            super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if not router.allow_migrate(schema_editor.connection.alias, app_label, **self.hints):
            return
        if schema_editor.collect_sql:
            schema_editor.collected_sql.append("-- Conditional reverse SQL: preserve an existing UNIQUE(code1c) constraint.")
            return super().database_backwards(app_label, schema_editor, from_state, to_state)
        if not has_unique_code1c(schema_editor):
            super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("placement_order", "0004_alter_placementorder_managers_placementorder_code1c_and_more")]

    operations = [
        RunSQLUnlessCode1cUnique(
            'DROP INDEX CONCURRENTLY IF EXISTS "placement_order_code1c_uniq"',
            reverse_sql=migrations.RunSQL.noop,
        ),
        RunSQLUnlessCode1cUnique(
            'CREATE UNIQUE INDEX CONCURRENTLY "placement_order_code1c_uniq" ON "placement_order_placementorder" ("code1c")',
            reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS "placement_order_code1c_uniq"',
        ),
        RunSQLUnlessCode1cUnique(
            'DROP INDEX CONCURRENTLY IF EXISTS "placement_order_code1c_like_idx"',
            reverse_sql=migrations.RunSQL.noop,
        ),
        RunSQLUnlessCode1cUnique(
            'CREATE INDEX CONCURRENTLY "placement_order_code1c_like_idx" ON "placement_order_placementorder" ("code1c" varchar_pattern_ops)',
            reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS "placement_order_code1c_like_idx"',
        ),
    ]
