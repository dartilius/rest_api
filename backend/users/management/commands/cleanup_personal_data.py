"""Explicit, dry-run-first CLI for the same cleanup used by Celery beat."""
import json

from django.core.management.base import BaseCommand

from users.tasks import cleanup_personal_data


class Command(BaseCommand):
    help = 'Count privacy cleanup candidates; --execute deletes one bounded batch.'

    def add_arguments(self, parser):
        parser.add_argument('--execute', action='store_true')
        parser.add_argument('--batch-size', type=int, default=500)

    def handle(self, *args, **options):
        result = cleanup_personal_data(
            dry_run=not options['execute'], batch_size=options['batch_size'],
        )
        self.stdout.write(json.dumps(result))
