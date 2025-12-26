"""
Management command to migrate legacy CSV data to the new Richtato platform.

Usage:
    python manage.py migrate_legacy_data --source-dir richtato_tep_data/ --user-id 1
    python manage.py migrate_legacy_data --dry-run --verbose
"""

import csv
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional

from apps.budget.models import Budget, BudgetCategory
from apps.financial_account.models import (
    AccountBalanceHistory,
    FinancialAccount,
    FinancialInstitution,
)
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory
from apps.transaction.signals import transaction_post_save
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction
from django.db.models.signals import post_save
from django.utils.text import slugify


class Command(BaseCommand):
    help = "Migrate legacy CSV data to the new Richtato platform"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ID mapping dictionaries
        self.account_id_map: Dict[int, int] = {}
        self.card_to_account_map: Dict[int, int] = {}
        self.category_id_map: Dict[int, int] = {}
        self.institution_map: Dict[str, FinancialInstitution] = {}
        self.new_user: Optional[User] = None
        self.dry_run = False
        self.verbose = False

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            type=str,
            default="richtato_tep_data/",
            help="Path to legacy CSV directory (default: richtato_tep_data/)",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            default=1,
            help="Legacy user ID to migrate (default: 1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without committing to database",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Detailed logging of each record",
        )
        parser.add_argument(
            "--target-username",
            type=str,
            default=None,
            help="Username for the new user (defaults to legacy username)",
        )

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"])
        legacy_user_id = options["user_id"]
        self.dry_run = options["dry_run"]
        self.verbose = options["verbose"]
        target_username = options.get("target_username")

        if not source_dir.exists():
            raise CommandError(f"Source directory does not exist: {source_dir}")

        # Validate required CSV files exist
        required_files = [
            "user.csv",
            "account.csv",
            "cards.csv",
            "category.csv",
            "income.csv",
            "expense.csv",
            "account_transaction.csv",
            "budget.csv",
        ]
        for filename in required_files:
            if not (source_dir / filename).exists():
                raise CommandError(f"Required file not found: {source_dir / filename}")

        self.stdout.write(self.style.NOTICE(f"Starting migration from {source_dir}"))
        self.stdout.write(self.style.NOTICE(f"Legacy user ID: {legacy_user_id}"))
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be saved")
            )

        try:
            with db_transaction.atomic():
                # Step 1: Create User
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write("Step 1: Creating User")
                self.stdout.write("=" * 50)
                self.import_user(source_dir, legacy_user_id, target_username)

                # Step 2: Import Financial Institutions
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write("Step 2: Importing Financial Institutions")
                self.stdout.write("=" * 50)
                self.import_institutions(source_dir, legacy_user_id)

                # Step 3: Import Financial Accounts
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write("Step 3: Importing Financial Accounts")
                self.stdout.write("=" * 50)
                self.import_accounts(source_dir, legacy_user_id)

                # Step 4: Import Transaction Categories
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write("Step 4: Importing Transaction Categories")
                self.stdout.write("=" * 50)
                self.import_categories(source_dir, legacy_user_id)

                # Step 5: Import Transactions
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write("Step 5: Importing Transactions")
                self.stdout.write("=" * 50)
                self.import_transactions(source_dir, legacy_user_id)

                # Step 6: Import Account Balance History
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write("Step 6: Importing Account Balance History")
                self.stdout.write("=" * 50)
                self.import_balance_history(source_dir, legacy_user_id)

                # Step 7: Import Budgets
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write("Step 7: Importing Budgets")
                self.stdout.write("=" * 50)
                self.import_budgets(source_dir, legacy_user_id)

                if self.dry_run:
                    self.stdout.write(
                        self.style.WARNING("\nDRY RUN - Rolling back all changes")
                    )
                    raise DryRunRollback()

        except DryRunRollback:
            pass

        self.stdout.write(self.style.SUCCESS("\nMigration completed successfully!"))
        self._print_summary()

    def _print_summary(self):
        """Print migration summary."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("MIGRATION SUMMARY")
        self.stdout.write("=" * 50)
        self.stdout.write(
            f"Accounts migrated: {len(self.account_id_map) + len(self.card_to_account_map)}"
        )
        self.stdout.write(f"  - Bank accounts: {len(self.account_id_map)}")
        self.stdout.write(f"  - Credit cards: {len(self.card_to_account_map)}")
        self.stdout.write(f"Categories migrated: {len(self.category_id_map)}")
        self.stdout.write(f"Institutions created: {len(self.institution_map)}")

    def _read_csv(self, filepath: Path) -> list:
        """Read CSV file and return list of dictionaries."""
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _log_verbose(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            self.stdout.write(f"  {message}")

    # =========================================================================
    # Step 1: Import User
    # =========================================================================
    def import_user(
        self, source_dir: Path, legacy_user_id: int, target_username: Optional[str]
    ):
        """Create a new user based on legacy user data."""
        users = self._read_csv(source_dir / "user.csv")
        legacy_user = None

        for user in users:
            if int(user["id"]) == legacy_user_id:
                legacy_user = user
                break

        if not legacy_user:
            raise CommandError(f"User with ID {legacy_user_id} not found in user.csv")

        username = target_username or legacy_user["username"]

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.new_user = User.objects.get(username=username)
            self.stdout.write(
                self.style.WARNING(
                    f"User '{username}' already exists, using existing user"
                )
            )
        else:
            self.new_user = User.objects.create_user(
                username=username,
                email=legacy_user.get("email") or None,
                password="changeme123",  # User should change password after migration
            )
            self.stdout.write(self.style.SUCCESS(f"Created user: {username}"))

        self._log_verbose(f"User ID mapping: {legacy_user_id} -> {self.new_user.id}")

    # =========================================================================
    # Step 2: Import Financial Institutions
    # =========================================================================
    def import_institutions(self, source_dir: Path, legacy_user_id: int):
        """Extract and create FinancialInstitutions from bank names in cards.csv."""
        cards = self._read_csv(source_dir / "cards.csv")
        bank_names = set()

        for card in cards:
            if int(card["user_id"]) == legacy_user_id:
                bank = card.get("bank", "").strip()
                if bank:
                    bank_names.add(bank)

        # Also extract from account.csv asset_entity_name
        accounts = self._read_csv(source_dir / "account.csv")
        for account in accounts:
            if int(account["user_id"]) == legacy_user_id:
                entity = account.get("asset_entity_name", "").strip()
                if entity and entity != "other":
                    bank_names.add(entity)

        # Normalize bank names
        bank_name_map = {
            "american_express": "American Express",
            "American Express": "American Express",
            "bank_of_america": "Bank of America",
            "Bank of America": "Bank of America",
            "chase": "Chase",
            "Chase": "Chase",
            "citibank": "Citibank",
            "Citibank": "Citibank",
            "bilt": "BILT",
            "BILT": "BILT",
        }

        created_count = 0
        for bank in bank_names:
            normalized_name = bank_name_map.get(bank, bank.replace("_", " ").title())
            slug = slugify(normalized_name)

            # Try to get by name first (unique constraint), then by slug
            try:
                institution = FinancialInstitution.objects.get(name=normalized_name)
                created = False
            except FinancialInstitution.DoesNotExist:
                try:
                    institution = FinancialInstitution.objects.get(slug=slug)
                    created = False
                except FinancialInstitution.DoesNotExist:
                    institution = FinancialInstitution.objects.create(
                        slug=slug,
                        name=normalized_name,
                    )
                    created = True

            self.institution_map[bank] = institution
            self.institution_map[normalized_name] = institution

            if created:
                created_count += 1
                self._log_verbose(f"Created institution: {normalized_name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Institutions: {created_count} created, {len(bank_names)} total"
            )
        )

    # =========================================================================
    # Step 3: Import Financial Accounts
    # =========================================================================
    def import_accounts(self, source_dir: Path, legacy_user_id: int):
        """Import FinancialAccounts from account.csv and cards.csv."""
        # Import bank/savings/investment accounts from account.csv
        accounts = self._read_csv(source_dir / "account.csv")
        account_count = 0

        for account in accounts:
            if int(account["user_id"]) != legacy_user_id:
                continue

            old_id = int(account["id"])
            account_type = account["type"]

            # Map account types
            type_mapping = {
                "checking": "checking",
                "savings": "savings",
                "investment": "savings",  # Map to savings as per plan
                "retirement": "savings",  # Map to savings as per plan
            }
            new_type = type_mapping.get(account_type, "savings")

            # Get institution if available
            entity_name = account.get("asset_entity_name", "").strip()
            institution = self.institution_map.get(entity_name)

            balance = Decimal(account.get("latest_balance", "0") or "0")

            new_account = FinancialAccount.objects.create(
                user=self.new_user,
                name=account["name"],
                account_type=new_type,
                balance=balance,
                institution=institution,
                is_active=True,
                is_liability=False,
                sync_source="csv",
            )

            self.account_id_map[old_id] = new_account.id
            account_count += 1
            self._log_verbose(
                f"Account: {account['name']} (type: {account_type} -> {new_type})"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Bank accounts imported: {account_count}")
        )

        # Import credit cards from cards.csv
        cards = self._read_csv(source_dir / "cards.csv")
        card_count = 0

        for card in cards:
            if int(card["user_id"]) != legacy_user_id:
                continue

            old_id = int(card["id"])
            bank = card.get("bank", "").strip()
            institution = self.institution_map.get(bank)

            new_account = FinancialAccount.objects.create(
                user=self.new_user,
                name=card["name"],
                account_type="credit_card",
                balance=Decimal("0"),
                institution=institution,
                is_active=True,
                is_liability=True,  # Credit cards are liabilities
                sync_source="csv",
            )

            self.card_to_account_map[old_id] = new_account.id
            card_count += 1
            self._log_verbose(f"Credit card: {card['name']} ({bank})")

        self.stdout.write(self.style.SUCCESS(f"Credit cards imported: {card_count}"))

    # =========================================================================
    # Step 4: Import Transaction Categories
    # =========================================================================
    def import_categories(self, source_dir: Path, legacy_user_id: int):
        """Import TransactionCategories from category.csv."""
        categories = self._read_csv(source_dir / "category.csv")
        count = 0

        for category in categories:
            if int(category["user_id"]) != legacy_user_id:
                continue

            old_id = int(category["id"])
            name = category["name"]
            old_type = category.get("type", "essential")  # essential or nonessential
            enabled = category.get("enabled", "true").lower() == "true"

            # Generate unique slug
            base_slug = slugify(name)
            slug = base_slug
            suffix = 1
            while TransactionCategory.objects.filter(
                user=self.new_user, slug=slug
            ).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1

            # Map old type to new type (all are expense categories)
            # Store the essential/nonessential distinction in icon
            icon = "💰" if old_type == "essential" else "🎯"

            new_category = TransactionCategory.objects.create(
                user=self.new_user,
                name=name,
                slug=slug,
                type="expense",  # All legacy categories are expense type
                icon=icon,
                color="#6366f1" if old_type == "essential" else "#8b5cf6",
            )

            self.category_id_map[old_id] = new_category.id
            count += 1
            self._log_verbose(f"Category: {name} (slug: {slug}, type: {old_type})")

        # Create an "Income" category for income transactions
        income_category, _ = TransactionCategory.objects.get_or_create(
            user=self.new_user,
            slug="income",
            defaults={
                "name": "Income",
                "type": "income",
                "icon": "💵",
                "color": "#22c55e",
            },
        )
        self.category_id_map["income"] = income_category.id

        self.stdout.write(self.style.SUCCESS(f"Categories imported: {count}"))

    # =========================================================================
    # Step 5: Import Transactions
    # =========================================================================
    def import_transactions(self, source_dir: Path, legacy_user_id: int):
        """Import Transactions from income.csv and expense.csv."""
        # Disable signals during bulk import for performance
        post_save.disconnect(transaction_post_save, sender=Transaction)

        try:
            # Import income transactions
            income_records = self._read_csv(source_dir / "income.csv")
            income_transactions = []
            income_count = 0
            income_category_id = self.category_id_map.get("income")

            for record in income_records:
                if int(record["user_id"]) != legacy_user_id:
                    continue

                old_account_id = int(record["account_name_id"])
                new_account_id = self.account_id_map.get(old_account_id)

                if not new_account_id:
                    self._log_verbose(
                        f"Skipping income: account {old_account_id} not found"
                    )
                    continue

                amount = Decimal(record["amount"])
                if amount <= 0:
                    continue

                income_transactions.append(
                    Transaction(
                        user=self.new_user,
                        account_id=new_account_id,
                        date=record["date"],
                        amount=amount,
                        description=record["description"],
                        transaction_type="credit",  # Income is credit
                        category_id=income_category_id,
                        status="posted",
                        sync_source="csv",
                        categorization_status="categorized",
                    )
                )
                income_count += 1
                self._log_verbose(f"Income: {record['description']} - ${amount}")

            # Bulk create income transactions
            if income_transactions:
                self.stdout.write(
                    f"  Creating {len(income_transactions)} income transactions..."
                )
                Transaction.objects.bulk_create(income_transactions, batch_size=500)
            self.stdout.write(
                self.style.SUCCESS(f"Income transactions imported: {income_count}")
            )

            # Import expense transactions
            expense_records = self._read_csv(source_dir / "expense.csv")
            expense_transactions = []
            expense_count = 0

            for record in expense_records:
                if int(record["user_id"]) != legacy_user_id:
                    continue

                old_account_id = int(record["account_name_id"])
                old_category_id = int(record["category_id"])

                # Check if this is a card or bank account
                new_account_id = self.account_id_map.get(old_account_id)
                if not new_account_id:
                    new_account_id = self.card_to_account_map.get(old_account_id)

                if not new_account_id:
                    self._log_verbose(
                        f"Skipping expense: account {old_account_id} not found"
                    )
                    continue

                new_category_id = self.category_id_map.get(old_category_id)
                if not new_category_id:
                    # Use uncategorized
                    new_category_id = None

                # Amount in old system is negative for expenses, make positive
                amount = Decimal(record["amount"])
                if amount < 0:
                    amount = abs(amount)

                # Determine transaction type based on sign
                # Negative amounts in old system = expense (debit)
                # Positive amounts in old system = refund (credit)
                original_amount = Decimal(record["amount"])
                if original_amount < 0:
                    transaction_type = "debit"
                else:
                    transaction_type = "credit"

                expense_transactions.append(
                    Transaction(
                        user=self.new_user,
                        account_id=new_account_id,
                        date=record["date"],
                        amount=amount,
                        description=record["description"],
                        transaction_type=transaction_type,
                        category_id=new_category_id,
                        status="posted",
                        sync_source="csv",
                        categorization_status="categorized"
                        if new_category_id
                        else "uncategorized",
                        notes=record.get("details", "")
                        if record.get("details") != "{}"
                        else "",
                    )
                )
                expense_count += 1
                self._log_verbose(f"Expense: {record['description']} - ${amount}")

            # Bulk create expense transactions
            if expense_transactions:
                self.stdout.write(
                    f"  Creating {len(expense_transactions)} expense transactions..."
                )
                Transaction.objects.bulk_create(expense_transactions, batch_size=500)
            self.stdout.write(
                self.style.SUCCESS(f"Expense transactions imported: {expense_count}")
            )

        finally:
            # Re-enable signals
            post_save.connect(transaction_post_save, sender=Transaction)
            # Note: Balance history is imported from CSV in Step 6, no recalculation needed

    # =========================================================================
    # Step 6: Import Account Balance History
    # =========================================================================
    def import_balance_history(self, source_dir: Path, legacy_user_id: int):
        """Import AccountBalanceHistory from account_transaction.csv."""
        records = self._read_csv(source_dir / "account_transaction.csv")
        count = 0
        skipped = 0

        for record in records:
            old_account_id = int(record["account_id"])

            # Get new account ID
            new_account_id = self.account_id_map.get(old_account_id)
            if not new_account_id:
                new_account_id = self.card_to_account_map.get(old_account_id)

            if not new_account_id:
                skipped += 1
                continue

            amount = Decimal(record["amount"])
            date = record["date"]

            # Check for duplicate (same account, same date)
            if AccountBalanceHistory.objects.filter(
                account_id=new_account_id, date=date
            ).exists():
                self._log_verbose(
                    f"Skipping duplicate balance history: account {new_account_id} on {date}"
                )
                skipped += 1
                continue

            AccountBalanceHistory.objects.create(
                account_id=new_account_id,
                date=date,
                balance=amount,
            )

            count += 1
            self._log_verbose(
                f"Balance history: account {old_account_id} on {date} = ${amount}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Balance history imported: {count} (skipped: {skipped})"
            )
        )

    # =========================================================================
    # Step 7: Import Budgets
    # =========================================================================
    def import_budgets(self, source_dir: Path, legacy_user_id: int):
        """Import Budgets from budget.csv."""
        records = self._read_csv(source_dir / "budget.csv")
        budget_count = 0
        allocation_count = 0

        # Group budget records by start_date to create budget periods
        budgets_by_date: Dict[str, list] = {}

        for record in records:
            if int(record["user_id"]) != legacy_user_id:
                continue

            start_date = record["start_date"]
            if start_date not in budgets_by_date:
                budgets_by_date[start_date] = []
            budgets_by_date[start_date].append(record)

        for start_date, allocations in budgets_by_date.items():
            # Determine end date (use first record's end_date if available, else end of month)
            end_date = allocations[0].get("end_date", "").strip()
            if not end_date:
                # Default to end of month
                from calendar import monthrange
                from datetime import datetime, timedelta

                dt = datetime.strptime(start_date, "%Y-%m-%d")
                last_day = monthrange(dt.year, dt.month)[1]
                end_date = dt.replace(day=last_day).strftime("%Y-%m-%d")

            # Create budget
            budget_name = f"Budget {start_date[:7]}"  # e.g., "Budget 2025-07"
            budget = Budget.objects.create(
                user=self.new_user,
                name=budget_name,
                period_type="monthly",
                start_date=start_date,
                end_date=end_date,
                is_active=True,
            )
            budget_count += 1
            self._log_verbose(f"Budget: {budget_name} ({start_date} to {end_date})")

            # Create category allocations
            for alloc in allocations:
                old_category_id = int(alloc["category_id"])
                new_category_id = self.category_id_map.get(old_category_id)

                if not new_category_id:
                    self._log_verbose(
                        f"Skipping budget allocation: category {old_category_id} not found"
                    )
                    continue

                amount = Decimal(alloc["amount"])

                BudgetCategory.objects.create(
                    budget=budget,
                    category_id=new_category_id,
                    allocated_amount=amount,
                )
                allocation_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Budgets imported: {budget_count} budgets with {allocation_count} allocations"
            )
        )


class DryRunRollback(Exception):
    """Exception to trigger rollback in dry-run mode."""

    pass
