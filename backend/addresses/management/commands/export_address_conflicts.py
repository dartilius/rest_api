import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from addresses.deduplication import address_metadata_conflicts


class Command(BaseCommand):
    help = "Exports metadata conflicts from duplicate physical addresses to CSV."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True, help="CSV path inside the backend container")

    def handle(self, *args, **options):
        output = Path(options["output"])
        if output.exists():
            raise CommandError(f"Refusing to overwrite existing file: {output}")

        conflicts = address_metadata_conflicts()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=(
                    "canonical_id",
                    "address_ids",
                    "conflict_fields",
                    "values",
                    "nomenclature_links",
                    "counterparty_links",
                ),
            )
            writer.writeheader()
            for conflict in conflicts:
                writer.writerow(
                    {
                        **conflict,
                        "address_ids": json.dumps(conflict["address_ids"], ensure_ascii=False),
                        "conflict_fields": json.dumps(conflict["conflict_fields"], ensure_ascii=False),
                        "values": json.dumps(conflict["values"], ensure_ascii=False),
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"Exported {len(conflicts)} conflict groups to {output}"))
