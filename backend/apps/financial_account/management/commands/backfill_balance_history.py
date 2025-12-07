"""Management command to backfill AccountBalanceHistory from transactions."""

from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.transaction.models import Transaction


class Command(BaseCommand):
    help = (
        "Backfill AccountBalanceHistory for all accounts based on transaction history"
    )

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
        parser.add_argument(
            "--account-id",
            type=int,
            help="Only backfill for a specific account ID",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear existing balance history before backfilling",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        user_id = options.get("user_id")
        account_id = options.get("account_id")
        clear_existing = options.get("clear_existing")

        # Get accounts to process
        accounts = FinancialAccount.objects.filter(is_active=True)

        if user_id:
            accounts = accounts.filter(user_id=user_id)

        if account_id:
            accounts = accounts.filter(id=account_id)

        total_accounts = accounts.count()
        total_records_created = 0
        accounts_processed = 0

        self.stdout.write(f"Processing {total_accounts} accounts...")

        for account in accounts:
            accounts_processed += 1
            records_created = self._process_account(
                account, dry_run, clear_existing, options["verbosity"]
            )
            total_records_created += records_created

            if options["verbosity"] >= 1 and accounts_processed % 10 == 0:
                self.stdout.write(
                    f"  Processed {accounts_processed}/{total_accounts} accounts..."
                )

        self.stdout.write("")
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would create {total_records_created} balance history records "
                    f"for {accounts_processed} accounts"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {total_records_created} balance history records "
                    f"for {accounts_processed} accounts"
                )
            )

    def _process_account(
        self,
        account: FinancialAccount,
        dry_run: bool,
        clear_existing: bool,
        verbosity: int,
    ) -> int:
        """
        Process a single account, creating balance history from transactions.

        Uses the current account balance as an anchor and works backwards
        to calculate historical balances.

        Returns the number of records created.
        """
        # Clear existing history if requested
        if clear_existing:
            if not dry_run:
                deleted_count = AccountBalanceHistory.objects.filter(
                    account=account
                ).delete()[0]
                if verbosity >= 2:
                    self.stdout.write(
                        f"  Cleared {deleted_count} existing history records for {account.name}"
                    )

        # Get all unique transaction dates for this account, sorted
        transaction_dates = (
            Transaction.objects.filter(account=account)
            .values_list("date", flat=True)
            .distinct()
            .order_by("date")
        )

        transaction_dates = list(transaction_dates)

        if not transaction_dates:
            if verbosity >= 2:
                self.stdout.write(
                    f"  Skipping {account.name} (ID: {account.id}) - no transactions"
                )
            return 0

        # Use current account balance as the anchor
        current_balance = account.balance

        if verbosity >= 2:
            self.stdout.write(
                f"  Processing {account.name} (ID: {account.id}): "
                f"anchor balance = {current_balance}, {len(transaction_dates)} transaction dates"
            )

        records_created = 0

        # Calculate balance at each transaction date by working backwards from anchor
        for target_date in transaction_dates:
            # Calculate net transactions AFTER target_date
            credits_after = Transaction.objects.filter(
                account=account, date__gt=target_date, transaction_type="credit"
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
            debits_after = Transaction.objects.filter(
                account=account, date__gt=target_date, transaction_type="debit"
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

            # Balance at target_date = current balance - net change since then
            net_change_after = credits_after - debits_after
            balance_at_date = current_balance - net_change_after

            if dry_run:
                if verbosity >= 2:
                    self.stdout.write(
                        f"  [DRY RUN] Would create: {account.name} on {target_date}: {balance_at_date}"
                    )
            else:
                AccountBalanceHistory.objects.update_or_create(
                    account=account,
                    date=target_date,
                    defaults={"balance": balance_at_date},
                )
                if verbosity >= 3:
                    self.stdout.write(
                        f"  Created: {account.name} on {target_date}: {balance_at_date}"
                    )

            records_created += 1

        if not dry_run and verbosity >= 2:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Completed {account.name} (ID: {account.id}): "
                    f"{records_created} balance history records created"
                )
            )

        return records_created
