"""Management command to backfill AccountBalanceHistory for existing accounts."""

from datetime import date

from django.core.management.base import BaseCommand

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount


class Command(BaseCommand):
    help = "Backfill AccountBalanceHistory for accounts that have a balance but no history records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Only backfill for a specific user ID",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        user_id = options.get("user_id")

        # Get all active accounts
        accounts = FinancialAccount.objects.filter(is_active=True)

        if user_id:
            accounts = accounts.filter(user_id=user_id)

        created_count = 0
        skipped_count = 0

        for account in accounts:
            # Check if account already has any balance history
            has_history = AccountBalanceHistory.objects.filter(account=account).exists()

            if has_history:
                skipped_count += 1
                if options["verbosity"] >= 2:
                    self.stdout.write(
                        f"  Skipping {account.name} (ID: {account.id}) - already has history"
                    )
                continue

            # Only create history if account has a non-zero balance
            if account.balance == 0:
                skipped_count += 1
                if options["verbosity"] >= 2:
                    self.stdout.write(
                        f"  Skipping {account.name} (ID: {account.id}) - zero balance"
                    )
                continue

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [DRY RUN] Would create history for {account.name} "
                        f"(ID: {account.id}): {account.balance}"
                    )
                )
            else:
                # Create initial balance history record for today
                AccountBalanceHistory.objects.create(
                    account=account,
                    date=date.today(),
                    balance=account.balance,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created history for {account.name} "
                        f"(ID: {account.id}): {account.balance}"
                    )
                )

            created_count += 1

        self.stdout.write("")
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would create {created_count} balance history records, "
                    f"skipped {skipped_count} accounts"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {created_count} balance history records, "
                    f"skipped {skipped_count} accounts"
                )
            )
