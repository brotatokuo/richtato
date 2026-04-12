"""Repository for FinancialAccount model."""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from django.db.models import Prefetch

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.richtato_user.models import User


class FinancialAccountRepository:
    """Repository for financial account data access."""

    def get_by_id(self, account_id: int) -> Optional[FinancialAccount]:
        """Get account by ID."""
        try:
            return (
                FinancialAccount.objects.select_related("institution", "user")
                .prefetch_related("sync_connections")
                .get(id=account_id)
            )
        except FinancialAccount.DoesNotExist:
            return None

    def get_by_user(
        self, user: User, is_active: Optional[bool] = None
    ) -> List[FinancialAccount]:
        """Get all accounts for a user."""
        queryset = (
            FinancialAccount.objects.filter(user=user)
            .select_related("institution")
            .prefetch_related("sync_connections")
        )
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        return list(queryset.all())

    def get_by_type(
        self, user: User, account_type: str, is_active: bool = True
    ) -> List[FinancialAccount]:
        """Get accounts by type for a user."""
        return list(
            FinancialAccount.objects.filter(
                user=user, account_type=account_type, is_active=is_active
            )
            .select_related("institution")
            .prefetch_related("sync_connections")
            .all()
        )

    def create_account(
        self,
        user: User,
        name: str,
        account_type: str,
        sync_source: str = "manual",
        institution=None,
        account_number_last4: str = "",
        balance: Decimal = Decimal("0"),
        currency: str = "USD",
    ) -> FinancialAccount:
        """Create a new financial account."""
        account = FinancialAccount.objects.create(
            user=user,
            name=name,
            account_type=account_type,
            sync_source=sync_source,
            institution=institution,
            account_number_last4=account_number_last4,
            balance=balance,
            currency=currency,
            is_active=True,
        )
        return account

    def update_account(self, account: FinancialAccount, **kwargs) -> FinancialAccount:
        """Update account fields."""
        for key, value in kwargs.items():
            if hasattr(account, key):
                setattr(account, key, value)
        account.save()
        return account

    def update_balance(
        self,
        account: FinancialAccount,
        balance: Decimal,
        balance_date: date = None,
        source: str = "transaction",
    ) -> FinancialAccount:
        """Update account balance and record history."""
        account.balance = balance
        account.save()

        if balance_date is None:
            balance_date = date.today()

        AccountBalanceHistory.objects.update_or_create(
            account=account,
            date=balance_date,
            defaults={"balance": balance, "source": source},
        )

        return account

    def delete_account(self, account: FinancialAccount) -> None:
        """Delete an account (soft delete by setting inactive)."""
        account.is_active = False
        account.save()

    def hard_delete_account(self, account: FinancialAccount) -> None:
        """Permanently delete an account."""
        account.delete()

    def get_balance_history(
        self, account: FinancialAccount, start_date: date = None, end_date: date = None
    ) -> List[AccountBalanceHistory]:
        """Get balance history for an account."""
        queryset = AccountBalanceHistory.objects.filter(account=account)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        return list(queryset.all())
