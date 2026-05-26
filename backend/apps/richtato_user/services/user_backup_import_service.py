"""Import user backup bundles onto fresh accounts."""

from __future__ import annotations

from typing import Any

from django.db import transaction as db_transaction

from apps.budget.models import Budget, BudgetCategory
from apps.financial_account.models import FinancialAccount
from apps.financial_account.repositories.institution_repository import FinancialInstitutionRepository
from apps.richtato_user.models import User, UserPreference
from apps.richtato_user.serializers import UserPreferenceSerializer
from apps.richtato_user.services.user_backup_schema import (
    parse_date,
    parse_decimal,
    summarize_bundle,
    validate_bundle_structure,
    validate_references,
)
from apps.transaction.models import CategoryKeyword, Transaction, TransactionCategory
from apps.transaction.services.bulk_transaction_service import bulk_create_restore_transactions


class UserBackupImportService:
    """Restore a v1 backup bundle onto an empty user account."""

    def __init__(self):
        self.institution_repository = FinancialInstitutionRepository()

    def can_import(self, user: User) -> tuple[bool, str | None]:
        if FinancialAccount.objects.filter(user=user).exists():
            return False, "Import is only available before any accounts are created."
        if Transaction.objects.filter(user=user).exists():
            return False, "Import is only available before any transactions exist."
        return True, None

    def preview(self, user: User, bundle: dict[str, Any]) -> dict[str, Any]:
        can_import, reason = self.can_import(user)
        structure_errors = validate_bundle_structure(bundle)
        reference_errors, warnings = validate_references(bundle) if not structure_errors else ([], [])

        errors = list(structure_errors)
        if not can_import and reason:
            errors.append(reason)
        errors.extend(reference_errors)

        counts = summarize_bundle(bundle) if isinstance(bundle, dict) else {}
        source_profile = (bundle.get("profile") or {}) if isinstance(bundle, dict) else {}

        return {
            "valid": len(errors) == 0,
            "can_import": can_import,
            "errors": errors,
            "warnings": warnings,
            "counts": counts,
            "source_profile": {
                "username": source_profile.get("username", ""),
                "email": source_profile.get("email", ""),
            },
        }

    def commit(self, user: User, bundle: dict[str, Any]) -> dict[str, Any]:
        preview = self.preview(user, bundle)
        if not preview["valid"]:
            raise ValueError("; ".join(preview["errors"]))

        counts = {
            "categories": 0,
            "keywords": 0,
            "budgets": 0,
            "budget_allocations": 0,
            "accounts": 0,
            "transactions": 0,
        }

        with db_transaction.atomic():
            CategoryKeyword.objects.filter(user=user).delete()
            TransactionCategory.objects.filter(user=user).delete()

            category_map = self._import_categories(user, bundle.get("categories") or [], counts)
            self._import_preferences(user, bundle.get("preferences") or {})
            account_map = self._import_accounts(user, bundle.get("accounts") or [], counts)
            self._import_budgets(user, bundle.get("budgets") or [], category_map, counts)
            self._import_transactions(user, bundle.get("transactions") or [], account_map, category_map, counts)

        return {"imported": counts}

    def _import_preferences(self, user: User, preferences: dict[str, Any]) -> None:
        if not preferences:
            return

        prefs, _created = UserPreference.objects.get_or_create(user=user)
        serializer = UserPreferenceSerializer(prefs, data=preferences, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def _import_categories(
        self,
        user: User,
        categories: list[dict[str, Any]],
        counts: dict[str, int],
    ) -> dict[str, TransactionCategory]:
        pending = list(categories)
        category_map: dict[str, TransactionCategory] = {}
        keywords_by_slug: dict[str, list[str]] = {}

        while pending:
            progress = False
            next_pending: list[dict[str, Any]] = []

            for item in pending:
                slug = item.get("slug")
                parent_slug = item.get("parent_slug")
                if not isinstance(slug, str):
                    continue

                if parent_slug and parent_slug not in category_map:
                    next_pending.append(item)
                    continue

                parent = category_map.get(parent_slug) if parent_slug else None
                category = TransactionCategory.objects.create(
                    user=user,
                    slug=slug,
                    name=item.get("name") or slug,
                    type=item.get("type") or "expense",
                    icon=item.get("icon") or "",
                    color=item.get("color") or "",
                    parent=parent,
                    expense_priority=item.get("expense_priority"),
                    is_deleted=bool(item.get("is_deleted", False)),
                )
                category_map[slug] = category
                counts["categories"] += 1
                keywords_by_slug[slug] = list(item.get("keywords") or [])
                progress = True

            if not progress:
                raise ValueError("Unable to resolve category parent relationships during import")
            pending = next_pending

        for slug, keywords in keywords_by_slug.items():
            category = category_map[slug]
            for keyword in keywords:
                CategoryKeyword.objects.create(user=user, category=category, keyword=str(keyword))
                counts["keywords"] += 1

        return category_map

    def _import_accounts(
        self,
        user: User,
        accounts: list[dict[str, Any]],
        counts: dict[str, int],
    ) -> dict[str, FinancialAccount]:
        account_map: dict[str, FinancialAccount] = {}

        for item in accounts:
            key = item.get("key")
            if not isinstance(key, str):
                continue

            institution_slug = item.get("institution") or "other"
            institution = self.institution_repository.resolve_for_slug(str(institution_slug))

            balance = parse_decimal(item.get("balance"), "balance")
            account = FinancialAccount.objects.create(
                user=user,
                name=item.get("name") or key,
                institution=institution,
                account_type=item.get("account_type") or "checking",
                currency=item.get("currency") or "USD",
                is_liability=bool(item.get("is_liability", False)),
                balance=balance,
                sync_mode=item.get("sync_mode") or "manual",
                agent_cadence=item.get("agent_cadence") or "daily",
                agent_sync_hour=int(item.get("agent_sync_hour") or 6),
                shared_with_household=bool(item.get("shared_with_household", False)),
                account_number_last4=item.get("account_number_last4") or "",
            )
            account_map[key] = account
            counts["accounts"] += 1

        return account_map

    def _import_budgets(
        self,
        user: User,
        budgets: list[dict[str, Any]],
        category_map: dict[str, TransactionCategory],
        counts: dict[str, int],
    ) -> None:
        for item in budgets:
            budget = Budget.objects.create(
                user=user,
                name=item.get("name") or "Imported Budget",
                period_type=item.get("period_type") or "monthly",
                start_date=parse_date(item.get("start_date"), "start_date"),
                end_date=parse_date(item.get("end_date"), "end_date"),
                is_active=bool(item.get("is_active", True)),
                is_household=bool(item.get("is_household", False)),
            )
            counts["budgets"] += 1

            for allocation in item.get("allocations") or []:
                category_slug = allocation.get("category_slug")
                category = category_map.get(category_slug)
                if not category:
                    continue

                BudgetCategory.objects.create(
                    budget=budget,
                    category=category,
                    allocated_amount=parse_decimal(allocation.get("allocated_amount"), "allocated_amount"),
                    rollover_enabled=bool(allocation.get("rollover_enabled", False)),
                    rollover_amount=parse_decimal(allocation.get("rollover_amount"), "rollover_amount"),
                )
                counts["budget_allocations"] += 1

    def _import_transactions(
        self,
        user: User,
        transactions: list[dict[str, Any]],
        account_map: dict[str, FinancialAccount],
        category_map: dict[str, TransactionCategory],
        counts: dict[str, int],
    ) -> None:
        by_account: dict[int, list[Transaction]] = {}

        for item in transactions:
            account_key = item.get("account_key")
            account = account_map.get(account_key)
            if not account:
                continue

            category_slug = item.get("category_slug")
            category = category_map.get(category_slug) if category_slug else None

            txn = Transaction(
                user=user,
                account=account,
                date=parse_date(item.get("date"), "date"),
                amount=parse_decimal(item.get("amount"), "amount"),
                description=str(item.get("description") or "")[:500],
                transaction_type=item.get("transaction_type") or "debit",
                category=category,
                status=item.get("status") or "posted",
                notes=item.get("notes") or "",
                sync_source=item.get("sync_source") or "manual",
                external_id=str(item.get("external_id") or "")[:255],
                is_recurring=bool(item.get("is_recurring", False)),
                categorization_status=item.get("categorization_status") or "uncategorized",
            )
            by_account.setdefault(account.id, []).append(txn)

        for account_id, account_transactions in by_account.items():
            account = FinancialAccount.objects.get(pk=account_id)
            created = bulk_create_restore_transactions(account, account_transactions)
            counts["transactions"] += created
