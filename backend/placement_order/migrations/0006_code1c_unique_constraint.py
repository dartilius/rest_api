from django.db import migrations, models, router


def has_unique_code1c(schema_editor):
    # Keep the historical operation independent of current application models.
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


class RestoreIndexUnlessCode1cUnique(migrations.RunSQL):
    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if not router.allow_migrate(schema_editor.connection.alias, app_label, **self.hints):
            return
        if schema_editor.collect_sql:
            schema_editor.collected_sql.append("-- Conditional reverse SQL: restore the owned index only without an existing UNIQUE(code1c).")
            return super().database_backwards(app_label, schema_editor, from_state, to_state)
        if not has_unique_code1c(schema_editor):
            super().database_backwards(app_label, schema_editor, from_state, to_state)


class AttachCode1cConstraint(migrations.RunSQL):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if not router.allow_migrate(schema_editor.connection.alias, app_label, **self.hints):
            return
        if schema_editor.collect_sql:
            schema_editor.collected_sql.append("-- Conditional SQL: attach the owned index only without an existing UNIQUE(code1c).")
            return super().database_forwards(app_label, schema_editor, from_state, to_state)
        if not has_unique_code1c(schema_editor):
            super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if not router.allow_migrate(schema_editor.connection.alias, app_label, **self.hints):
            return
        if schema_editor.collect_sql:
            schema_editor.collected_sql.append("-- Conditional reverse SQL: drop only the migration-owned UNIQUE(code1c) constraint.")
            return super().database_backwards(app_label, schema_editor, from_state, to_state)
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_constraint c
                    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attname = 'code1c'
                    JOIN pg_index i ON i.indexrelid = c.conindid
                    WHERE c.conrelid = to_regclass('placement_order_placementorder')
                      AND c.conname = 'placement_order_code1c_uniq'
                      AND c.contype = 'u' AND c.conkey = ARRAY[a.attnum]
                      AND i.indisvalid AND i.indisunique
                )
            """)
            owned_constraint = cursor.fetchone()[0]
        if owned_constraint:
            super().database_backwards(app_label, schema_editor, from_state, to_state)


class AtomicDatabaseAndState(migrations.SeparateDatabaseAndState):
    """Keep SET LOCAL and short DDL in one transaction, even on rollback."""

    atomic = True


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("placement_order", "0005_code1c_indexes_concurrently")]

    operations = [
        # DROP CONSTRAINT also drops its owned index. Restore the 0005 schema
        # on reversal outside a transaction so 0006 can be applied again.
        RestoreIndexUnlessCode1cUnique(
            migrations.RunSQL.noop,
            reverse_sql=[
                'DROP INDEX CONCURRENTLY IF EXISTS "placement_order_code1c_uniq"',
                'CREATE UNIQUE INDEX CONCURRENTLY "placement_order_code1c_uniq" '
                'ON "placement_order_placementorder" ("code1c")',
            ],
        ),
        AtomicDatabaseAndState(
            database_operations=[
                AttachCode1cConstraint(
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
