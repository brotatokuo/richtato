"""Import tepolak from raw table JSON exports.

This is a one-off migration command for exports produced from an older
Richtato database. It imports only the requested user and remaps all foreign
keys into the current schema.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction
from django.utils.dateparse import parse_datetime

from apps.budget.models import Budget, BudgetCategory
from apps.financial_account.models import AccountBalanceHistory, FinancialAccount, FinancialInstitution
from apps.richtato_user.models import User
from apps.transaction.models import CategoryKeyword, Transaction, TransactionCategory


class Command(BaseCommand):
    help = "Import only tepolak from raw JSON table exports"

    file_names = {
        "users": "richtato_user_user.json",
        "institutions": "financial_institution.json",
        "accounts": "financial_account.json",
        "categories": "transaction_category.json",
        "transactions": "transaction.json",
        "budgets": "budget.json",
        "budget_categories": "budget_category.json",
        "balance_history": "account_balance_history.json",
    }

    account_sync_sources = {"manual", "csv"}
    transaction_sync_sources = {"manual", "csv"}
    balance_history_sources = {"transaction", "manual", "csv_import", "agent_sync"}
    transaction_types = {"debit", "credit"}
    transaction_statuses = {"pending", "posted", "reconciled"}
    categorization_statuses = {"uncategorized", "pending_ai", "categorized"}

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            default="/Users/alankuo/Downloads",
            help="Directory containing the raw JSON export files.",
        )
        parser.add_argument(
            "--username",
            default="tepolak",
            help="Username to import from the raw user export.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and summarize without writing to the database.",
        )

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"]).expanduser()
        username = options["username"]
        dry_run = options["dry_run"]

        data = self._load_source_files(source_dir)
        source = self._build_source_scope(data, username)
        self._validate_source(source, username)

        if User.objects.filter(username=username).exists():
            raise CommandError(f"Target user already exists: {username}")

        self._print_source_summary(source, dry_run=dry_run)
        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry run passed. No database changes were made."))
            return

        with db_transaction.atomic():
            counts = self._import_source(source)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Import complete."))
        for key, value in counts.items():
            self.stdout.write(f"  - {key}: {value}")

    def _load_source_files(self, source_dir: Path) -> dict[str, list[dict[str, Any]]]:
        if not source_dir.exists():
            raise CommandError(f"Source directory does not exist: {source_dir}")

        loaded: dict[str, list[dict[str, Any]]] = {}
        for key, file_name in self.file_names.items():
            path = source_dir / file_name
            if not path.exists():
                raise CommandError(f"Missing source file: {path}")
            try:
                contents = json.loads(path.read_text())
            except json.JSONDecodeError as exc:
                raise CommandError(f"Invalid JSON in {path}: {exc}") from exc
            if not isinstance(contents, list):
                raise CommandError(f"Expected a JSON array in {path}")
            loaded[key] = contents
        return loaded

    def _build_source_scope(self, data: dict[str, list[dict[str, Any]]], username: str) -> dict[str, Any]:
        matching_users = [row for row in data["users"] if row.get("username") == username]
        if len(matching_users) != 1:
            raise CommandError(f"Expected exactly one source user named {username}; found {len(matching_users)}")

        user_row = matching_users[0]
        old_user_id = user_row["id"]

        accounts = [row for row in data["accounts"] if row.get("user_id") == old_user_id]
        account_ids = {row["id"] for row in accounts}

        categories = [row for row in data["categories"] if row.get("user_id") == old_user_id]
        category_ids = {row["id"] for row in categories}

        transactions = [row for row in data["transactions"] if row.get("user_id") == old_user_id]

        budgets = [row for row in data["budgets"] if row.get("user_id") == old_user_id]
        budget_ids = {row["id"] for row in budgets}

        budget_categories = [row for row in data["budget_categories"] if row.get("budget_id") in budget_ids]
        balance_history = [row for row in data["balance_history"] if row.get("account_id") in account_ids]

        institution_ids = {row.get("institution_id") for row in accounts if row.get("institution_id") is not None}
        institutions = [row for row in data["institutions"] if row.get("id") in institution_ids]

        return {
            "user": user_row,
            "old_user_id": old_user_id,
            "institutions": institutions,
            "accounts": accounts,
            "account_ids": account_ids,
            "categories": categories,
            "category_ids": category_ids,
            "transactions": transactions,
            "budgets": budgets,
            "budget_ids": budget_ids,
            "budget_categories": budget_categories,
            "balance_history": balance_history,
        }

    def _validate_source(self, source: dict[str, Any], username: str) -> None:
        errors: list[str] = []

        if source["user"].get("username") != username:
            errors.append("Scoped source user does not match requested username.")

        institution_ids = {row["id"] for row in source["institutions"]}
        for account in source["accounts"]:
            institution_id = account.get("institution_id")
            if institution_id is not None and institution_id not in institution_ids:
                errors.append(f"Account {account.get('id')} references missing institution {institution_id}.")

        category_ids = source["category_ids"]
        category_slugs: set[str] = set()
        for category in source["categories"]:
            slug = category.get("slug")
            if not slug:
                errors.append(f"Category {category.get('id')} is missing a slug.")
            elif slug in category_slugs:
                errors.append(f"Duplicate source category slug for {username}: {slug}.")
            category_slugs.add(slug)

            parent_id = category.get("parent_id")
            if parent_id is not None and parent_id not in category_ids:
                errors.append(f"Category {category.get('id')} references missing parent {parent_id}.")

        account_ids = source["account_ids"]
        for txn in source["transactions"]:
            if txn.get("account_id") not in account_ids:
                errors.append(f"Transaction {txn.get('id')} references missing account {txn.get('account_id')}.")
            category_id = txn.get("category_id")
            if category_id is not None and category_id not in category_ids:
                errors.append(f"Transaction {txn.get('id')} references missing category {category_id}.")
            self._parse_date(txn.get("date"), f"transaction {txn.get('id')} date")
            self._parse_decimal(txn.get("amount"), f"transaction {txn.get('id')} amount")

        budget_ids = source["budget_ids"]
        for budget in source["budgets"]:
            self._parse_date(budget.get("start_date"), f"budget {budget.get('id')} start_date")
            self._parse_date(budget.get("end_date"), f"budget {budget.get('id')} end_date")

        seen_budget_allocations: set[tuple[int, int]] = set()
        for allocation in source["budget_categories"]:
            budget_id = allocation.get("budget_id")
            category_id = allocation.get("category_id")
            if budget_id not in budget_ids:
                errors.append(f"Budget allocation {allocation.get('id')} references missing budget {budget_id}.")
            if category_id not in category_ids:
                errors.append(f"Budget allocation {allocation.get('id')} references missing category {category_id}.")
            allocation_key = (budget_id, category_id)
            if allocation_key in seen_budget_allocations:
                errors.append(f"Duplicate budget allocation for budget {budget_id} and category {category_id}.")
            seen_budget_allocations.add(allocation_key)
            self._parse_decimal(allocation.get("allocated_amount"), f"budget allocation {allocation.get('id')} amount")
            self._parse_decimal(allocation.get("rollover_amount"), f"budget allocation {allocation.get('id')} rollover")

        seen_history: set[tuple[int, str]] = set()
        for history in source["balance_history"]:
            account_id = history.get("account_id")
            if account_id not in account_ids:
                errors.append(f"Balance history {history.get('id')} references missing account {account_id}.")
            self._parse_date(history.get("date"), f"balance history {history.get('id')} date")
            history_key = (account_id, history.get("date"))
            if history_key in seen_history:
                errors.append(f"Duplicate balance history for account {account_id} on {history.get('date')}.")
            seen_history.add(history_key)
            self._parse_decimal(history.get("balance"), f"balance history {history.get('id')} balance")

        if errors:
            raise CommandError("\n".join(errors[:50]))

    def _print_source_summary(self, source: dict[str, Any], *, dry_run: bool) -> None:
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(f"{prefix}Import scope:")
        self.stdout.write(f"  - user: {source['user']['username']} (old id {source['old_user_id']})")
        self.stdout.write(f"  - institutions: {len(source['institutions'])}")
        self.stdout.write(f"  - accounts: {len(source['accounts'])}")
        self.stdout.write(f"  - categories: {len(source['categories'])}")
        self.stdout.write(f"  - transactions: {len(source['transactions'])}")
        self.stdout.write(f"  - budgets: {len(source['budgets'])}")
        self.stdout.write(f"  - budget allocations: {len(source['budget_categories'])}")
        self.stdout.write(f"  - balance history rows: {len(source['balance_history'])}")

    def _import_source(self, source: dict[str, Any]) -> dict[str, int]:
        user = self._create_user(source["user"])

        # User creation initializes defaults; replace them with the exported tree.
        CategoryKeyword.objects.filter(user=user).delete()
        TransactionCategory.objects.filter(user=user).delete()

        institution_map = self._import_institutions(source["institutions"])
        category_map = self._import_categories(user, source["categories"])
        account_map = self._import_accounts(user, source["accounts"], institution_map)
        transaction_count = self._import_transactions(user, source["transactions"], account_map, category_map)
        budget_map = self._import_budgets(user, source["budgets"])
        budget_category_count = self._import_budget_categories(source["budget_categories"], budget_map, category_map)
        balance_history_count = self._import_balance_history(source["balance_history"], account_map)

        return {
            "user": 1,
            "institutions_resolved": len(institution_map),
            "accounts": len(account_map),
            "categories": len(category_map),
            "transactions": transaction_count,
            "budgets": len(budget_map),
            "budget_allocations": budget_category_count,
            "balance_history": balance_history_count,
        }

    def _create_user(self, row: dict[str, Any]) -> User:
        user = User.objects.create(
            username=row["username"],
            password=row.get("password") or "",
            email=row.get("email"),
            last_login=self._parse_datetime(row.get("last_login")),
            is_active=bool(row.get("is_active", True)),
            is_staff=bool(row.get("is_staff", False)),
            is_superuser=bool(row.get("is_superuser", False)),
            import_path=row.get("import_path") or "",
            is_demo=bool(row.get("is_demo", False)),
            demo_expires_at=self._parse_datetime(row.get("demo_expires_at")),
        )
        self._update_model_timestamps(user, date_joined=row.get("date_joined"))
        user.refresh_from_db()
        return user

    def _import_institutions(self, rows: list[dict[str, Any]]) -> dict[int, FinancialInstitution]:
        institution_map: dict[int, FinancialInstitution] = {}
        for row in rows:
            slug = row.get("slug") or ""
            name = row.get("name") or slug
            institution = FinancialInstitution.objects.filter(slug=slug).first()
            if institution is None:
                institution = FinancialInstitution.objects.filter(name=name).first()
            if institution is None:
                institution = FinancialInstitution.objects.create(
                    name=name,
                    slug=slug,
                    logo_url=row.get("logo_url"),
                    support_url=row.get("support_url"),
                )
                self._update_model_timestamps(
                    institution,
                    created_at=row.get("created_at"),
                    updated_at=row.get("updated_at"),
                )
            institution_map[row["id"]] = institution
        return institution_map

    def _import_categories(self, user: User, rows: list[dict[str, Any]]) -> dict[int, TransactionCategory]:
        pending = sorted(rows, key=lambda row: (row.get("parent_id") is not None, row.get("id")))
        category_map: dict[int, TransactionCategory] = {}

        while pending:
            next_pending: list[dict[str, Any]] = []
            progress = False
            for row in pending:
                parent_id = row.get("parent_id")
                if parent_id is not None and parent_id not in category_map:
                    next_pending.append(row)
                    continue

                category = TransactionCategory.objects.create(
                    user=user,
                    name=row.get("name") or row.get("slug") or "Imported Category",
                    slug=row.get("slug"),
                    icon=row.get("icon") or "",
                    color=row.get("color") or "",
                    type=row.get("type") or "expense",
                    parent=category_map.get(parent_id),
                    expense_priority=row.get("expense_priority"),
                    is_deleted=bool(row.get("is_deleted", False)),
                )
                if row.get("expense_priority") is None:
                    TransactionCategory.objects.filter(pk=category.pk).update(expense_priority=None)
                    category.expense_priority = None
                self._update_model_timestamps(category, created_at=row.get("created_at"))
                category_map[row["id"]] = category
                progress = True

            if not progress:
                raise CommandError("Unable to resolve category parent relationships.")
            pending = next_pending

        return category_map

    def _import_accounts(
        self,
        user: User,
        rows: list[dict[str, Any]],
        institution_map: dict[int, FinancialInstitution],
    ) -> dict[int, FinancialAccount]:
        account_map: dict[int, FinancialAccount] = {}
        for row in rows:
            institution_id = row.get("institution_id")
            account = FinancialAccount.objects.create(
                user=user,
                name=row.get("name") or "Imported Account",
                institution=institution_map.get(institution_id) if institution_id is not None else None,
                account_number_last4=self._last4(row.get("account_number_last4")),
                account_type=row.get("account_type") or "checking",
                balance=self._parse_decimal(row.get("balance"), f"account {row.get('id')} balance"),
                currency=row.get("currency") or "USD",
                is_active=bool(row.get("is_active", True)),
                is_liability=bool(row.get("is_liability", False)),
                sync_source=self._normalize_sync_source(row.get("sync_source"), self.account_sync_sources),
                sync_mode="manual",
                shared_with_household=False,
                storage_uri="",
            )
            self._update_model_timestamps(
                account,
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
            )
            account_map[row["id"]] = account
        return account_map

    def _import_transactions(
        self,
        user: User,
        rows: list[dict[str, Any]],
        account_map: dict[int, FinancialAccount],
        category_map: dict[int, TransactionCategory],
    ) -> int:
        transactions = [
            Transaction(
                user=user,
                account=account_map[row["account_id"]],
                date=self._parse_date(row.get("date"), f"transaction {row.get('id')} date"),
                amount=self._parse_decimal(row.get("amount"), f"transaction {row.get('id')} amount"),
                description=str(row.get("description") or "")[:500],
                transaction_type=self._choice(row.get("transaction_type"), self.transaction_types, "debit"),
                status=self._choice(row.get("status"), self.transaction_statuses, "posted"),
                is_recurring=bool(row.get("is_recurring", False)),
                sync_source=self._normalize_sync_source(row.get("sync_source"), self.transaction_sync_sources),
                external_id=str(row.get("external_id") or "")[:255],
                raw_data=row.get("raw_data"),
                categorization_status=self._choice(
                    row.get("categorization_status"),
                    self.categorization_statuses,
                    "uncategorized",
                ),
                notes=row.get("notes") or "",
                category=category_map.get(row.get("category_id")),
            )
            for row in rows
        ]
        Transaction.objects.bulk_create(transactions, batch_size=500)
        return len(transactions)

    def _import_budgets(self, user: User, rows: list[dict[str, Any]]) -> dict[int, Budget]:
        budget_map: dict[int, Budget] = {}
        for row in rows:
            budget = Budget.objects.create(
                user=user,
                name=row.get("name") or "Imported Budget",
                period_type=row.get("period_type") or "monthly",
                start_date=self._parse_date(row.get("start_date"), f"budget {row.get('id')} start_date"),
                end_date=self._parse_date(row.get("end_date"), f"budget {row.get('id')} end_date"),
                is_active=bool(row.get("is_active", True)),
                is_household=False,
            )
            self._update_model_timestamps(
                budget,
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
            )
            budget_map[row["id"]] = budget
        return budget_map

    def _import_budget_categories(
        self,
        rows: list[dict[str, Any]],
        budget_map: dict[int, Budget],
        category_map: dict[int, TransactionCategory],
    ) -> int:
        allocations = [
            BudgetCategory(
                budget=budget_map[row["budget_id"]],
                category=category_map[row["category_id"]],
                allocated_amount=self._parse_decimal(
                    row.get("allocated_amount"),
                    f"budget allocation {row.get('id')} amount",
                ),
                rollover_enabled=bool(row.get("rollover_enabled", False)),
                rollover_amount=self._parse_decimal(
                    row.get("rollover_amount"),
                    f"budget allocation {row.get('id')} rollover",
                ),
            )
            for row in rows
        ]
        BudgetCategory.objects.bulk_create(allocations, batch_size=500)
        return len(allocations)

    def _import_balance_history(
        self,
        rows: list[dict[str, Any]],
        account_map: dict[int, FinancialAccount],
    ) -> int:
        history_rows = [
            AccountBalanceHistory(
                account=account_map[row["account_id"]],
                date=self._parse_date(row.get("date"), f"balance history {row.get('id')} date"),
                balance=self._parse_decimal(row.get("balance"), f"balance history {row.get('id')} balance"),
                source=self._normalize_balance_history_source(row.get("source")),
            )
            for row in rows
        ]
        AccountBalanceHistory.objects.bulk_create(history_rows, batch_size=500)
        return len(history_rows)

    def _parse_decimal(self, value: Any, field_name: str) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise CommandError(f"{field_name} is not a valid decimal: {value}") from exc

    def _parse_date(self, value: Any, field_name: str) -> date:
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except (TypeError, ValueError) as exc:
            raise CommandError(f"{field_name} is not a valid date: {value}") from exc

    def _parse_datetime(self, value: Any):
        if not value:
            return None
        parsed = parse_datetime(str(value))
        if parsed is None:
            raise CommandError(f"Invalid datetime: {value}")
        return parsed

    def _update_model_timestamps(self, instance, **values: Any) -> None:
        updates = {
            field: self._parse_datetime(value) for field, value in values.items() if value and hasattr(instance, field)
        }
        if updates:
            instance.__class__.objects.filter(pk=instance.pk).update(**updates)

    def _normalize_sync_source(self, value: Any, allowed: set[str]) -> str:
        value = str(value or "manual")
        if value in allowed:
            return value
        if value in {"plaid", "plaid_sync"}:
            return "manual"
        return "manual"

    def _normalize_balance_history_source(self, value: Any) -> str:
        value = str(value or "transaction")
        if value in self.balance_history_sources:
            return value
        if value in {"plaid", "plaid_sync"}:
            return "manual"
        if value == "csv":
            return "csv_import"
        return "transaction"

    def _choice(self, value: Any, allowed: set[str], default: str) -> str:
        value = str(value or default)
        return value if value in allowed else default

    def _last4(self, value: Any) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value[:4] if value else ""
