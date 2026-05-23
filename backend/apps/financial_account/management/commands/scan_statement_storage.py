"""Scan account storage URIs for new statement files and auto-import them.

Run manually or wire into cron / Celery beat. Idempotent: previously
imported files (matched by sha256) are skipped on every subsequent run.
"""

from django.core.management.base import BaseCommand

from apps.financial_account.services.storage_scanner_service import StorageScannerService


class Command(BaseCommand):
    help = "Discover and auto-import statement files dropped into account storage URIs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Discover files without creating StatementFile rows or importing transactions.",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Limit scan to a single user's accounts.",
        )
        parser.add_argument(
            "--account-id",
            type=int,
            help="Limit scan to a single account.",
        )
        parser.add_argument(
            "--verbose-outcomes",
            action="store_true",
            help="Print every per-file outcome (not just the summary).",
        )

    def handle(self, *args, **options):
        service = StorageScannerService()

        if options.get("account_id"):
            result = service.scan_account(options["account_id"], dry_run=options["dry_run"])
        elif options.get("user_id"):
            result = service.scan_user(options["user_id"], dry_run=options["dry_run"])
        else:
            result = service.scan_all(dry_run=options["dry_run"])

        self.stdout.write(self.style.SUCCESS("Storage scan complete"))
        self.stdout.write(f"  Accounts scanned: {result.accounts_scanned}")
        self.stdout.write(f"  Files seen:       {result.files_seen}")
        self.stdout.write(f"  Imported:         {result.files_imported}")
        self.stdout.write(f"  Skipped:          {result.files_skipped}")
        self.stdout.write(f"  Failed:           {result.files_failed}")
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("  (dry-run: nothing was written)"))

        if options.get("verbose_outcomes"):
            self.stdout.write("")
            self.stdout.write("Per-file outcomes:")
            for outcome in result.outcomes:
                line = f"  [{outcome.status}] account={outcome.account_id} {outcome.relative_path}"
                if outcome.detail:
                    line += f" :: {outcome.detail}"
                self.stdout.write(line)
