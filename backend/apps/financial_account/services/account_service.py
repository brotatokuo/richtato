"""Service for account business logic."""

from datetime import date
from decimal import Decimal

from loguru import logger

from apps.financial_account.models import FinancialAccount
from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from apps.financial_account.repositories.institution_repository import (
    FinancialInstitutionRepository,
)
from apps.richtato_user.models import User

OPENING_BALANCE_DESCRIPTION = "Opening Balance"
_MISSING = object()


class AccountService:
    """Service for account management business logic."""

    def __init__(self):
        self.account_repository = FinancialAccountRepository()
        self.institution_repository = FinancialInstitutionRepository()

    def get_user_accounts(self, user: User, active_only: bool = True) -> list[FinancialAccount]:
        """Get all accounts for a user."""
        return self.account_repository.get_by_user(user, is_active=active_only if active_only else None)

    def get_household_accounts(
        self,
        user_ids: list[int],
        active_only: bool = True,
    ) -> list[FinancialAccount]:
        """Get shared accounts for a set of household member user IDs."""
        return self.account_repository.get_by_user_ids_shared(
            user_ids,
            is_active=active_only if active_only else None,
        )

    def get_account_by_id(
        self,
        account_id: int,
        user: User,
        household_user_ids: list[int] | None = None,
    ) -> FinancialAccount | None:
        """Get account by ID, ensuring it belongs to the user or their household."""
        account = self.account_repository.get_by_id(account_id)
        if not account:
            return None
        if account.user == user:
            return account
        if household_user_ids and account.user_id in household_user_ids and account.shared_with_household:
            return account
        return None

    def get_accounts_by_type(self, user: User, account_type: str) -> list[FinancialAccount]:
        """Get accounts of a specific type."""
        return self.account_repository.get_by_type(user, account_type)

    def create_manual_account(
        self,
        user: User,
        name: str,
        account_type: str,
        institution_name: str = None,
        institution_slug: str = None,
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
            institution_name: Optional bank/institution name (for synced accounts)
            institution_slug: Optional institution slug (for manually selected preset banks)
            account_number_last4: Last 4 digits of account number
            initial_balance: Starting balance
            currency: Currency code

        Returns:
            Created FinancialAccount instance
        """
        # Get or create institution if provided
        institution = None

        # First try to look up by slug (for preset banks selected from dropdown)
        if institution_slug and institution_slug != "other":
            institution = self.institution_repository.get_by_slug(institution_slug)

        # If no slug match, try by name (for synced accounts or custom entries)
        if not institution and institution_name:
            slug = institution_name.lower().replace(" ", "_").replace("-", "_")
            institution = self.institution_repository.get_or_create_institution(name=institution_name, slug=slug)

        account = self.account_repository.create_account(
            user=user,
            name=name,
            account_type=account_type,
            sync_source="manual",
            institution=institution,
            account_number_last4=account_number_last4,
            balance=Decimal("0"),
            currency=currency,
        )

        if account_type == "credit_card":
            account.is_liability = True
            account.save(update_fields=["is_liability"])

        if initial_balance != Decimal("0"):
            self.upsert_opening_balance(account, initial_balance)

        logger.info(f"Created manual account {account.id} for user {user.username}: {name}")

        self._provision_drive_folder(user, account)

        return account

    def _provision_drive_folder(self, user: User, account: FinancialAccount) -> None:
        """Create a Google Drive folder for a new account if Drive storage is active."""
        from apps.financial_account.models import GoogleDriveConnection
        from apps.financial_account.services.google_drive_activation_service import (
            GoogleDriveActivationService,
        )

        connection = GoogleDriveConnection.objects.filter(user=user, is_active=True).first()
        if not connection:
            return
        try:
            drive_svc = GoogleDriveActivationService()
            folder = drive_svc._create_account_folder(connection, account)
            account.storage_uri = f"gdrive://{folder.folder_id}"
            account.save(update_fields=["storage_uri", "updated_at"])
            logger.info(
                "Provisioned Drive folder {} for new account {}",
                folder.folder_id,
                account.id,
            )
        except Exception:
            logger.exception(
                "Failed to create Drive folder for account {}",
                account.id,
            )

    def get_opening_balance_transaction(self, account: FinancialAccount):
        """Return the account's Opening Balance transaction, if one exists."""
        from apps.transaction.models import Transaction

        return Transaction.objects.filter(
            account=account,
            description=OPENING_BALANCE_DESCRIPTION,
        ).first()

    def get_opening_balance(self, account: FinancialAccount) -> tuple[Decimal | None, date | None]:
        """Return signed opening balance amount and its date."""
        transaction = self.get_opening_balance_transaction(account)
        if transaction is None:
            return None, None
        return transaction.signed_amount, transaction.date

    def upsert_opening_balance(
        self,
        account: FinancialAccount,
        balance: Decimal,
        balance_date: date | None = None,
    ):
        """Create or update the Opening Balance transaction for an account."""
        from apps.transaction.models import Transaction

        if balance_date is None:
            balance_date = date.today()

        if balance > 0:
            txn_type = "credit"
            amount = balance
        elif balance < 0:
            txn_type = "debit"
            amount = abs(balance)
        else:
            self.delete_opening_balance(account)
            return None

        existing = self.get_opening_balance_transaction(account)
        if existing is None:
            return Transaction.objects.create(
                user=account.user,
                account=account,
                date=balance_date,
                amount=amount,
                transaction_type=txn_type,
                description=OPENING_BALANCE_DESCRIPTION,
                sync_source="manual",
                status="reconciled",
            )

        existing.date = balance_date
        existing.amount = amount
        existing.transaction_type = txn_type
        existing.save(update_fields=["date", "amount", "transaction_type", "updated_at"])
        return existing

    def delete_opening_balance(self, account: FinancialAccount) -> None:
        """Remove the Opening Balance transaction for an account."""
        existing = self.get_opening_balance_transaction(account)
        if existing is not None:
            existing.delete()

    def update_account(self, account: FinancialAccount, **kwargs) -> FinancialAccount:
        """Update account fields."""
        opening_balance = kwargs.pop("opening_balance", _MISSING)
        opening_balance_date = kwargs.pop("opening_balance_date", None)

        # Handle institution name update
        if "institution_name" in kwargs:
            institution_name = kwargs.pop("institution_name")
            if institution_name:
                slug = institution_name.lower().replace(" ", "_").replace("-", "_")
                institution = self.institution_repository.get_or_create_institution(name=institution_name, slug=slug)
                kwargs["institution"] = institution
            else:
                kwargs["institution"] = None

        updated_account = self.account_repository.update_account(account, **kwargs)

        if opening_balance is not _MISSING:
            if opening_balance is None:
                logger.info(
                    "Deleting opening balance",
                    account_id=updated_account.id,
                )
                self.delete_opening_balance(updated_account)
            else:
                parsed_date = opening_balance_date
                if isinstance(parsed_date, str):
                    parsed_date = date.fromisoformat(parsed_date)
                logger.info(
                    "Upserting opening balance",
                    account_id=updated_account.id,
                    opening_balance=str(opening_balance),
                    opening_balance_date=str(parsed_date),
                )
                self.upsert_opening_balance(
                    updated_account,
                    Decimal(str(opening_balance)),
                    parsed_date,
                )
            updated_account.refresh_from_db()
            balance, balance_date = self.get_opening_balance(updated_account)
            logger.info(
                "Opening balance persisted",
                account_id=updated_account.id,
                account_balance=str(updated_account.balance),
                opening_balance=str(balance) if balance is not None else None,
                opening_balance_date=balance_date.isoformat() if balance_date else None,
            )
        else:
            logger.debug(
                "Account update without opening balance change",
                account_id=updated_account.id,
            )

        return updated_account

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

    def get_account_summary(self, user: User) -> dict:
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
