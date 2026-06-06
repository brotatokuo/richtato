"""Export user data as JSON backup bundles and transaction CSV files."""

from __future__ import annotations

import csv
import io
from datetime import date

from django.utils.text import slugify

from apps.budget.models import Budget
from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User, UserPreference
from apps.richtato_user.services.user_backup_schema import (
    BACKUP_APP_NAME,
    BACKUP_FORMAT_VERSION,
    exported_at_iso,
)
from apps.richtato_user.services.user_service import UserService
from apps.transaction.models import Transaction, TransactionCategory


class UserBackupExportService:
    """Build portable JSON and CSV exports for a user's personal data."""

    def __init__(self, user_service: UserService | None = None):
        self.user_service = user_service or UserService()

    def build_json_bundle(self, user: User) -> dict:
        preferences = self._export_preferences(user)
        categories = self._export_categories(user)
        accounts, account_key_by_id = self._export_accounts(user)
        budgets = self._export_budgets(user)
        transactions = self._export_transactions(user, account_key_by_id)
        profile = self.user_service.get_user_profile_data(user)

        return {
            "format_version": BACKUP_FORMAT_VERSION,
            "exported_at": exported_at_iso(),
            "app": BACKUP_APP_NAME,
            "profile": {
                "username": profile.get("username", user.username),
                "email": profile.get("email", user.email or ""),
            },
            "preferences": preferences,
            "categories": categories,
            "budgets": budgets,
            "accounts": accounts,
            "transactions": transactions,
        }

    def build_transactions_csv(
        self,
        user: User,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        account_id: int | None = None,
    ) -> str:
        queryset = Transaction.objects.filter(user=user).select_related("account", "category").order_by("date", "id")
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if account_id:
            queryset = queryset.filter(account_id=account_id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "date",
                "amount",
                "type",
                "description",
                "account_name",
                "category_slug",
                "status",
                "notes",
                "sync_source",
                "external_id",
            ]
        )

        for txn in queryset.iterator(chunk_size=500):
            writer.writerow(
                [
                    txn.date.isoformat(),
                    str(txn.amount),
                    txn.transaction_type,
                    txn.description,
                    txn.account.name,
                    txn.category.slug if txn.category else "",
                    txn.status,
                    txn.notes or "",
                    txn.sync_source,
                    txn.external_id or "",
                ]
            )

        return output.getvalue()

    def _export_preferences(self, user: User) -> dict:
        try:
            prefs = UserPreference.objects.get(user=user)
        except UserPreference.DoesNotExist:
            return {
                "theme": "system",
                "currency": "USD",
                "date_format": "MM/DD/YYYY",
                "timezone": "UTC",
                "notifications_enabled": True,
                "platform_tour_completed": False,
            }

        return {
            "theme": prefs.theme,
            "currency": prefs.currency,
            "date_format": prefs.date_format,
            "timezone": prefs.timezone,
            "notifications_enabled": prefs.notifications_enabled,
            "platform_tour_completed": prefs.platform_tour_completed,
        }

    def _export_categories(self, user: User) -> list[dict]:
        categories = (
            TransactionCategory.objects.filter(user=user)
            .prefetch_related("keywords")
            .select_related("parent")
            .order_by("slug")
        )
        exported: list[dict] = []
        for category in categories:
            exported.append(
                {
                    "slug": category.slug,
                    "name": category.name,
                    "type": category.type,
                    "icon": category.icon or "",
                    "color": category.color or "",
                    "parent_slug": category.parent.slug if category.parent else None,
                    "expense_priority": category.expense_priority,
                    "is_deleted": category.is_deleted,
                    "keywords": sorted(keyword.keyword for keyword in category.keywords.all()),
                }
            )
        return exported

    def _export_budgets(self, user: User) -> list[dict]:
        budgets = (
            Budget.objects.filter(user=user, is_household=False)
            .prefetch_related("budget_categories__category")
            .order_by("-start_date")
        )
        exported: list[dict] = []
        for budget in budgets:
            allocations = []
            for allocation in budget.budget_categories.all():
                allocations.append(
                    {
                        "category_slug": allocation.category.slug,
                        "allocated_amount": str(allocation.allocated_amount),
                        "rollover_enabled": allocation.rollover_enabled,
                        "rollover_amount": str(allocation.rollover_amount),
                    }
                )
            exported.append(
                {
                    "name": budget.name,
                    "period_type": budget.period_type,
                    "start_date": budget.start_date.isoformat(),
                    "end_date": budget.end_date.isoformat(),
                    "is_active": budget.is_active,
                    "is_household": budget.is_household,
                    "allocations": allocations,
                }
            )
        return exported

    def _export_accounts(self, user: User) -> tuple[list[dict], dict[int, str]]:
        accounts = FinancialAccount.objects.filter(user=user).select_related("institution").order_by("id")
        exported: list[dict] = []
        key_by_id: dict[int, str] = {}
        used_keys: set[str] = set()

        for account in accounts:
            key = self._account_export_key(account, used_keys)
            used_keys.add(key)
            key_by_id[account.id] = key
            exported.append(
                {
                    "key": key,
                    "name": account.name,
                    "institution": account.institution.slug if account.institution else None,
                    "account_type": account.account_type,
                    "currency": account.currency,
                    "is_liability": account.is_liability,
                    "balance": str(account.balance),
                    "sync_mode": account.sync_mode,
                    "shared_with_household": account.shared_with_household,
                    "account_number_last4": account.account_number_last4 or "",
                }
            )

        return exported, key_by_id

    def _export_transactions(self, user: User, account_key_by_id: dict[int, str]) -> list[dict]:
        transactions = Transaction.objects.filter(user=user).select_related("category").order_by("date", "id")
        exported: list[dict] = []
        for txn in transactions.iterator(chunk_size=500):
            exported.append(
                {
                    "account_key": account_key_by_id[txn.account_id],
                    "date": txn.date.isoformat(),
                    "amount": str(txn.amount),
                    "description": txn.description,
                    "transaction_type": txn.transaction_type,
                    "category_slug": txn.category.slug if txn.category else None,
                    "status": txn.status,
                    "notes": txn.notes or "",
                    "sync_source": txn.sync_source,
                    "external_id": txn.external_id or "",
                    "is_recurring": txn.is_recurring,
                    "categorization_status": txn.categorization_status,
                }
            )
        return exported

    def _account_export_key(self, account: FinancialAccount, used_keys: set[str]) -> str:
        institution_part = account.institution.slug if account.institution else "manual"
        base = slugify(f"{account.name}-{institution_part}") or f"account-{account.id}"
        key = base
        suffix = 2
        while key in used_keys:
            key = f"{base}-{suffix}"
            suffix += 1
        return key
