"""Verify old file selections survive the change to a brand selector."""
import importlib
import unittest
from uuid import uuid4

from django.db import models
from django.db.migrations.state import ModelState, ProjectState
from django.db.utils import ConnectionHandler


class BrandLinkMigrationTests(unittest.TestCase):
    def test_preserves_file_links_and_creates_a_separate_brand_relation(self):
        connection = ConnectionHandler({"default": {
            "ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:",
        }})["default"]
        state = ProjectState()
        for app, name in (("files", "File"), ("brands", "Brand")):
            state.add_model(ModelState(app, name, [
                ("id", models.UUIDField(primary_key=True)),
            ], options={"db_table": f"migration_test_{app}"}))
        state.add_model(ModelState("corporate_broadcast", "BroadcastLanding", [
            ("id", models.AutoField(primary_key=True)),
            ("logo_brands", models.ManyToManyField("files.File", blank=True)),
        ], options={"db_table": "migration_test_landing"}))
        file_id = uuid4().hex
        brand_id = uuid4().hex
        operation = importlib.import_module(
            "corporate_broadcast.migrations.0003_landing_brand_links"
        ).Migration.operations[0]
        new_state = state.clone()
        operation.state_forwards("corporate_broadcast", new_state)
        try:
            with connection.schema_editor() as editor:
                for app, name in (("files", "File"), ("brands", "Brand"), ("corporate_broadcast", "BroadcastLanding")):
                    editor.create_model(state.apps.get_model(app, name))
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO migration_test_files (id) VALUES (%s)", [file_id])
                cursor.execute("INSERT INTO migration_test_brands (id) VALUES (%s)", [brand_id])
                cursor.execute("INSERT INTO migration_test_landing (id) VALUES (1)")
                cursor.execute("INSERT INTO migration_test_landing_logo_brands (broadcastlanding_id, file_id) VALUES (1, %s)", [file_id])
            with connection.schema_editor() as editor:
                operation.database_forwards("corporate_broadcast", editor, state, new_state)
            with connection.cursor() as cursor:
                cursor.execute("SELECT file_id FROM migration_test_landing_legacy_logo_files")
                self.assertEqual(cursor.fetchall(), [(file_id,)])
                cursor.execute("SELECT COUNT(*) FROM migration_test_landing_logo_brands")
                self.assertEqual(cursor.fetchone()[0], 0)
                cursor.execute("INSERT INTO migration_test_landing_logo_brands (broadcastlanding_id, brand_id) VALUES (1, %s)", [brand_id])
            with connection.schema_editor() as editor:
                operation.database_backwards("corporate_broadcast", editor, new_state, state)
            with connection.cursor() as cursor:
                cursor.execute("SELECT file_id FROM migration_test_landing_logo_brands")
                self.assertEqual(cursor.fetchall(), [(file_id,)])
        finally:
            connection.close()
