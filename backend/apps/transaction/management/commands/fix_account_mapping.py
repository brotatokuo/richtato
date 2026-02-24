"""
Management command to fix transaction account mappings based on CSV files.

The CSV files (expense.csv, income.csv) are the source of truth. This command:
1. Reads transaction descriptions, dates, and account_name_ids from the CSVs
2. Maps account_name_id to account names using account.csv
3. Finds matching FinancialAccount in DB by name
4. Matches transactions by description and date (since IDs differ between CSV and DB)
5. Updates transaction.account_id to the correct DB account ID
"""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Q
from loguru import logger

from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction


class Command(BaseCommand):
    help = "Fix transaction account mappings based on CSV source of truth"

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Actually commit changes to database (default is dry-run)",
        )
        parser.add_argument(
            "--username",
            type=str,
            default="tepolak",
            help="Username to fix transactions for (default: tepolak)",
        )
        parser.add_argument(
            "--csv-dir",
            type=str,
            default="/Users/alan/Desktop/Personal/richtato",
            help="Directory containing CSV files",
        )

    def handle(self, *args, **options):
        commit = options["commit"]
        username = options["username"]
        csv_dir = Path(options["csv_dir"])

        if not commit:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN MODE - no changes will be made. Use --commit to apply."
                )
            )

        # Get user
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f"Found user: {user.username} (DB id={user.id})")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{username}' not found"))
            return

        # Load cards.csv to build CSV account_id -> card name mapping
        cards_csv_path = csv_dir / "cards.csv"
        if not cards_csv_path.exists():
            self.stdout.write(
                self.style.ERROR(f"cards.csv not found at {cards_csv_path}")
            )
            return

        csv_id_to_name = {}
        with open(cards_csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only include cards for user_id=1 (tepolak in CSV)
                if row["user_id"] == "1":
                    csv_id_to_name[int(row["id"])] = row["name"]

        self.stdout.write(f"\nCSV card mappings from cards.csv (user_id=1):")
        for csv_id, name in sorted(csv_id_to_name.items()):
            self.stdout.write(f"  CSV id={csv_id} -> '{name}'")

        # Build account_name -> DB FinancialAccount.id mapping
        db_accounts = FinancialAccount.objects.filter(user=user)
        name_to_db_id = {}
        for acc in db_accounts:
            # Handle potential duplicate names by keeping first match
            if acc.name not in name_to_db_id:
                name_to_db_id[acc.name] = acc.id

        self.stdout.write(f"\nDB account mappings for {username}:")
        for name, db_id in sorted(name_to_db_id.items(), key=lambda x: x[1]):
            self.stdout.write(f"  '{name}' -> DB id={db_id}")

        # Build final mapping: CSV account_id -> DB account_id
        csv_id_to_db_id = {}
        missing_mappings = []
        for csv_id, name in csv_id_to_name.items():
            if name in name_to_db_id:
                csv_id_to_db_id[csv_id] = name_to_db_id[name]
            else:
                missing_mappings.append((csv_id, name))

        if missing_mappings:
            self.stdout.write(
                self.style.WARNING("\nMissing DB accounts for CSV mappings:")
            )
            for csv_id, name in missing_mappings:
                self.stdout.write(
                    f"  CSV id={csv_id} '{name}' - no matching DB account"
                )

        self.stdout.write(f"\nFinal mapping (CSV account_id -> DB account_id):")
        for csv_id, db_id in sorted(csv_id_to_db_id.items()):
            name = csv_id_to_name[csv_id]
            self.stdout.write(f"  CSV {csv_id} -> DB {db_id} ('{name}')")

        # Process expense.csv
        expense_csv_path = csv_dir / "expense.csv"
        income_csv_path = csv_dir / "income.csv"

        stats = {
            "total": 0,
            "updated": 0,
            "skipped_no_mapping": 0,
            "skipped_not_found": 0,
            "skipped_same": 0,
            "skipped_wrong_user": 0,
            "skipped_multiple_matches": 0,
        }

        # Process expenses
        if expense_csv_path.exists():
            self.stdout.write(f"\nProcessing {expense_csv_path}...")
            self._process_csv(
                expense_csv_path,
                csv_id_to_db_id,
                user,
                commit,
                stats,
                is_expense=True,
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"expense.csv not found at {expense_csv_path}")
            )

        # Process income
        if income_csv_path.exists():
            self.stdout.write(f"\nProcessing {income_csv_path}...")
            self._process_csv(
                income_csv_path,
                csv_id_to_db_id,
                user,
                commit,
                stats,
                is_expense=False,
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"income.csv not found at {income_csv_path}")
            )

        # Print summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Total transactions processed: {stats['total']}")
        self.stdout.write(self.style.SUCCESS(f"Updated: {stats['updated']}"))
        self.stdout.write(f"Skipped (already correct): {stats['skipped_same']}")
        self.stdout.write(f"Skipped (wrong user in CSV): {stats['skipped_wrong_user']}")
        self.stdout.write(
            f"Skipped (no account mapping): {stats['skipped_no_mapping']}"
        )
        self.stdout.write(
            f"Skipped (transaction not in DB): {stats['skipped_not_found']}"
        )
        self.stdout.write(
            f"Skipped (multiple matches): {stats['skipped_multiple_matches']}"
        )

        if not commit:
            self.stdout.write(
                self.style.WARNING(
                    "\nDRY RUN - no changes were made. Use --commit to apply."
                )
            )

    def _process_csv(
        self,
        csv_path: Path,
        csv_id_to_db_id: dict,
        user: User,
        commit: bool,
        stats: dict,
        is_expense: bool = True,
    ):
        """Process a CSV file and update transactions by matching on description and date."""
        account_field = "account_name_id"

        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats["total"] += 1

                # Check if this row is for user_id=1 (tepolak in CSV)
                csv_user_id = row.get("user_id", "")
                if csv_user_id != "1":
                    stats["skipped_wrong_user"] += 1
                    continue

                try:
                    description = row["description"].strip()
                    date_str = row["date"]
                    amount_str = row["amount"]
                    csv_account_id = int(row[account_field])

                    # Parse date
                    txn_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                    # Parse amount (expenses are negative in CSV, income positive)
                    amount = abs(Decimal(amount_str))

                except (ValueError, KeyError) as e:
                    logger.warning(f"Invalid row in CSV: {row}, error: {e}")
                    continue

                # Get target DB account ID
                if csv_account_id not in csv_id_to_db_id:
                    stats["skipped_no_mapping"] += 1
                    if stats["skipped_no_mapping"] <= 5:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  No mapping for CSV account_id={csv_account_id} "
                                f"(desc={description[:30]})"
                            )
                        )
                    continue

                target_db_account_id = csv_id_to_db_id[csv_account_id]

                # Find transaction in DB by description, date, and amount
                # Use case-insensitive description match
                txns = Transaction.objects.filter(
                    user=user,
                    date=txn_date,
                    amount=amount,
                ).filter(
                    Q(description__iexact=description)
                    | Q(description__icontains=description[:20])
                )

                if txns.count() == 0:
                    stats["skipped_not_found"] += 1
                    continue
                elif txns.count() > 1:
                    # Try to narrow down by exact description match
                    exact_match = txns.filter(description__iexact=description)
                    if exact_match.count() == 1:
                        txn = exact_match.first()
                    else:
                        stats["skipped_multiple_matches"] += 1
                        if stats["skipped_multiple_matches"] <= 5:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  Multiple matches for: {description[:30]} on {txn_date} "
                                    f"(${amount}) - found {txns.count()} transactions"
                                )
                            )
                        continue
                else:
                    txn = txns.first()

                # Check if update needed
                if txn.account_id == target_db_account_id:
                    stats["skipped_same"] += 1
                    continue

                # Update transaction
                old_account_id = txn.account_id
                old_account_name = txn.account.name if txn.account else "None"

                if commit:
                    txn.account_id = target_db_account_id
                    txn.save(update_fields=["account_id"])

                stats["updated"] += 1

                # Log change (limit output)
                if stats["updated"] <= 20:
                    new_account = FinancialAccount.objects.get(id=target_db_account_id)
                    self.stdout.write(
                        f"  {description[:30]:30} ({txn_date}): "
                        f"{old_account_name} -> {new_account.name}"
                    )
                elif stats["updated"] == 21:
                    self.stdout.write("  ... (more changes not shown)")
