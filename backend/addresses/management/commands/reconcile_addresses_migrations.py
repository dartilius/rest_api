from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = "Checks and, with --apply, records already-present address migrations 0002–0004."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_name = 'addresses_city' AND column_name = 'slug'"
            )
            slug = cursor.fetchone()
            cursor.execute("SELECT count(*) FROM addresses_city WHERE slug IS NULL OR slug = ''")
            missing_slugs = cursor.fetchone()[0]

        if slug != ("NO",) or missing_slugs:
            raise CommandError("Schema does not match addresses migrations 0002–0004; do not fake them.")

        self.stdout.write("addresses 0002–0004 are already present in the schema.")
        if not options["apply"]:
            self.stdout.write("Dry-run only. Run again with --apply to record migration history.")
            return

        recorder = MigrationRecorder(connection)
        applied = {
            name
            for app_label, name in recorder.applied_migrations()
            if app_label == "addresses"
        }
        for name in ("0002_city_slug", "0003_populate_city_slugs", "0004_city_slug_not_null"):
            if name not in applied:
                recorder.record_applied("addresses", name)
                self.stdout.write(self.style.SUCCESS(f"Recorded addresses.{name}"))
