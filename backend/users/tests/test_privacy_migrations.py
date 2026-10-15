from importlib import import_module

from django.db import connection, connections
from django.db.backends.sqlite3.base import DatabaseWrapper
from django.db.migrations.loader import MigrationLoader
from django.test import TransactionTestCase, override_settings
from django.utils import timezone


class PrivacyMigrationTests(TransactionTestCase):
    def test_real_forward_and_reverse_operations_preserve_legacy_records(self):
        # Apply the actual new DDL to historical models on a separate memory database.
        # Existing PG-only migration SQL is not executed against SQLite.
        with override_settings(MIGRATION_MODULES={}):
            loader = MigrationLoader(None)
        before = loader.project_state([
            ('users', '0003_passwordresetemailverification_and_more'),
            ('feedback', '0008_remove_redundant_production_indexes'),
        ])
        config = dict(connection.settings_dict, NAME=':memory:')
        db = DatabaseWrapper(config, alias='privacy_migration_memory')
        connections[db.alias] = db
        db.ensure_connection()
        try:
            models = [before.apps.get_model(app, name) for app, name in (
                ('users', 'CustomUser'), ('users', 'RegistrationEmailVerification'),
                ('placement_order', 'PlacementOrder'), ('feedback', 'Feedback'),
            )]
            with db.schema_editor() as editor:
                for model in models:
                    editor.create_model(model)
            # Raw insertion avoids resolving this private connection via the global router.
            with db.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO registration_email_verification '
                    '(email, code, expires_at, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)',
                    ['legacy@example.test', 'hash', timezone.now(), timezone.now(), timezone.now()],
                )
            migration_specs = [
                ('feedback', '0009_feedback_closed_at_feedback_contract_reference_and_more'),
                ('feedback', '0010_feedback_lawful_retention_basis_and_more'),
                ('users', '0004_registrationemailverification_last_consent_at_and_more'),
            ]
            history = []
            state = before.clone()
            for app, name in migration_specs:
                migration = import_module(f'{app}.migrations.{name}').Migration(name, app)
                history.append((migration, state.clone()))
                with db.schema_editor() as editor:
                    state = migration.apply(state, editor)
            with db.cursor() as cursor:
                cursor.execute('SELECT email, last_consent_at FROM registration_email_verification')
                self.assertEqual(cursor.fetchone(), ('legacy@example.test', None))
                columns = {col.name for col in db.introspection.get_table_description(cursor, 'feedback')}
                self.assertTrue({'closed_at', 'delete_after', 'contract_status'} <= columns)
            for migration, previous in reversed(history):
                with db.schema_editor() as editor:
                    migration.unapply(previous, editor)
            with db.cursor() as cursor:
                cursor.execute('SELECT email FROM registration_email_verification')
                self.assertEqual(cursor.fetchone()[0], 'legacy@example.test')
        finally:
            db.close()
            del connections[db.alias]
