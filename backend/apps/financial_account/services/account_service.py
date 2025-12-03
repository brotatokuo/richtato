"""Service for account business logic."""

from decimal import Decimal
from typing import Dict, List, Optional

from apps.financial_account.models import FinancialAccount
from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from apps.financial_account.repositories.institution_repository import (
    FinancialInstitutionRepository,
)
from apps.richtato_user.models import User
from loguru import logger


class AccountService:
    """Service for account management business logic."""

    def __init__(self):
        self.account_repository = FinancialAccountRepository()
        self.institution_repository = FinancialInstitutionRepository()

    def get_user_accounts(
        self, user: User, active_only: bool = True
    ) -> List[FinancialAccount]:
        """Get all accounts for a user."""
        return self.account_repository.get_by_user(
            user, is_active=active_only if active_only else None
        )

    def get_account_by_id(
        self, account_id: int, user: User
    ) -> Optional[FinancialAccount]:
        """Get account by ID, ensuring it belongs to the user."""
        account = self.account_repository.get_by_id(account_id)
        if account and account.user == user:
            return account
        return None

    def get_accounts_by_type(
        self, user: User, account_type: str
    ) -> List[FinancialAccount]:
        """Get accounts of a specific type."""
        return self.account_repository.get_by_type(user, account_type)

    def create_manual_account(
        self,
        user: User,
        name: str,
        account_type: str,
        institution_name: str = None,
        account_number_last4: str = "",
        initial_balance: Decimal = Decimal("0"),
        currency: str = "USD",
    ) -> FinancialAccount:
        """
        Create a manually entered account.

        Args:
            user: Account owner
            name: Account nickname/name
            account_type: Type (checking/savings/credit_card)
            institution_name: Optional bank/institution name
            account_number_last4: Last 4 digits of account number
            initial_balance: Starting balance
            currency: Currency code

        Returns:
            Created FinancialAccount instance
        """
        # Get or create institution if provided
        institution = None
        if institution_name:
            slug = institution_name.lower().replace(" ", "_")
            institution = self.institution_repository.get_or_create_institution(
                name=institution_name, slug=slug
            )

        account = self.account_repository.create_account(
            user=user,
            name=name,
            account_type=account_type,
            sync_source="manual",
            institution=institution,
            account_number_last4=account_number_last4,
            balance=initial_balance,
            currency=currency,
        )

        logger.info(
            f"Created manual account {account.id} for user {user.username}: {name}"
        )

        return account

    def update_account(self, account: FinancialAccount, **kwargs) -> FinancialAccount:
        """Update account fields."""
        # Handle institution name update
        if "institution_name" in kwargs:
            institution_name = kwargs.pop("institution_name")
            if institution_name:
                slug = institution_name.lower().replace(" ", "_")
                institution = self.institution_repository.get_or_create_institution(
                    name=institution_name, slug=slug
                )
                kwargs["institution"] = institution
            else:
                kwargs["institution"] = None

        return self.account_repository.update_account(account, **kwargs)

    def delete_account(self, account: FinancialAccount) -> bool:
        """
        Delete (deactivate) an account.

        Args:
            account: Account to delete

        Returns:
            True if successful
        """
        try:
            self.account_repository.delete_account(account)
            logger.info(f"Deactivated account {account.id}: {account.name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting account {account.id}: {str(e)}")
            return False

    def get_account_summary(self, user: User) -> Dict:
        """
        Get summary of all user accounts.

        Returns:
            Dict with account counts and total balances by type
        """
        accounts = self.get_user_accounts(user, active_only=True)

        summary = {
            "total_accounts": len(accounts),
            "checking": {"count": 0, "total_balance": Decimal("0")},
            "savings": {"count": 0, "total_balance": Decimal("0")},
            "credit_card": {"count": 0, "total_balance": Decimal("0")},
        }

        for account in accounts:
            if account.account_type in summary:
                summary[account.account_type]["count"] += 1
                summary[account.account_type]["total_balance"] += account.balance

        return summary
