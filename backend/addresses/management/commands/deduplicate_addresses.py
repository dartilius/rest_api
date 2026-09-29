from django.core.management.base import BaseCommand, CommandError

from addresses.deduplication import deduplicate_final_addresses


class Command(BaseCommand):
    help = (
        "Reports structurally duplicate final addresses and, with --apply, "
        "moves links before deleting safe duplicates."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply the merge. Without this flag the command is read-only.",
        )
        parser.add_argument(
            "--keep-canonical-metadata",
            action="store_true",
            help=(
                "Merge conflicting groups too, retaining metadata from the "
                "chosen canonical address. Requires --apply."
            ),
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        keep_canonical_metadata = options["keep_canonical_metadata"]
        if keep_canonical_metadata and not apply:
            raise CommandError("--keep-canonical-metadata requires --apply")

        mode = "APPLY" if apply else "DRY-RUN"
        self.stdout.write(f"Address duplicate consolidation: {mode}")

        results = deduplicate_final_addresses(
            apply=apply,
            allow_metadata_conflicts=keep_canonical_metadata,
        )
        if not results:
            self.stdout.write(self.style.SUCCESS("No structural duplicate groups found."))
            return

        removed_count = 0
        conflict_count = 0
        for result in results:
            if result.applied and result.metadata_conflicts:
                removed_count += len(result.duplicate_ids)
                state = "MERGED: canonical metadata retained for " + ", ".join(
                    result.metadata_conflicts
                )
            elif result.metadata_conflicts:
                conflict_count += 1
                state = "SKIPPED: metadata conflicts " + ", ".join(result.metadata_conflicts)
            elif result.applied:
                removed_count += len(result.duplicate_ids)
                state = "MERGED"
            else:
                state = "WOULD MERGE"

            self.stdout.write(
                " | ".join(
                    (
                        state,
                        f"canonical={result.canonical_id}",
                        f"duplicates={','.join(result.duplicate_ids)}",
                        f"nomenclature_links={result.nomenclature_links}",
                        f"counterparty_links={result.counterparty_links}",
                    )
                )
            )

        if apply:
            self.stdout.write(self.style.SUCCESS(f"Removed duplicate addresses: {removed_count}"))
        self.stdout.write(f"Groups with metadata conflicts: {conflict_count}")
