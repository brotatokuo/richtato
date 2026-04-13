"""Shared logic for creating FinancialAccount + SyncConnection from Plaid account data."""

from decimal import Decimal

from loguru import logger

from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from apps.financial_account.services.account_service import AccountService
from apps.sync.repositories.sync_connection_repository import SyncConnectionRepository

PLAID_TYPE_MAPPING = {
    "depository": "checking",
    "credit": "credit_card",
    "loan": "loan",
    "investment": "investment",
}


def map_plaid_account_type(account_type: str, account_subtype: str) -> str:
    if account_subtype in ("savings", "cd", "money market"):
        return "savings"
    if account_subtype == "checking":
        return "checking"
    if account_subtype == "credit card":
        return "credit_card"
    return PLAID_TYPE_MAPPING.get(account_type, "checking")


def extract_plaid_balance(plaid_account: dict) -> Decimal:
    try:
        balances = plaid_account.get("balances", {})
        current = balances.get("current") or balances.get("ledger")
        if current is not None:
            return Decimal(str(current))
    except Exception:
        pass
    return Decimal("0")


def create_plaid_financial_account(
    user,
    plaid_account: dict,
    access_token: str,
    institution_name: str,
    item_id: str,
    connection_repository: SyncConnectionRepository | None = None,
    account_service: AccountService | None = None,
    account_repository: FinancialAccountRepository | None = None,
):
    """Create a FinancialAccount and SyncConnection for a single Plaid account.

    Returns the SyncConnection if created (or the existing one), or None on error.
    """
    connection_repository = connection_repository or SyncConnectionRepository()
    account_service = account_service or AccountService()
    account_repository = account_repository or FinancialAccountRepository()

    plaid_account_id = plaid_account.get("id") or ""
    account_name = plaid_account.get("name", "Account")
    account_type = plaid_account.get("type", "depository")
    account_subtype = plaid_account.get("subtype", "")
    last_four = plaid_account.get("last_four", "")

    existing = connection_repository.get_by_external_account_id(user, "plaid", plaid_account_id)
    if existing:
        logger.info(f"Connection already exists for Plaid account {plaid_account_id}")
        return existing

    mapped_type = map_plaid_account_type(account_type, account_subtype)
    initial_balance = extract_plaid_balance(plaid_account)

    financial_account = account_service.create_manual_account(
        user=user,
        name=f"{institution_name} {account_name}",
        account_type=mapped_type,
        institution_name=institution_name,
        account_number_last4=last_four,
        initial_balance=initial_balance,
    )
    financial_account.sync_source = "plaid"
    if mapped_type in ("credit_card", "loan"):
        financial_account.is_liability = True
        if initial_balance > 0:
            initial_balance = -initial_balance
    financial_account.save()

    if initial_balance != Decimal("0"):
        account_repository.update_balance(financial_account, initial_balance)

    connection = connection_repository.create_connection(
        user=user,
        account=financial_account,
        provider="plaid",
        access_token=access_token,
        institution_name=institution_name,
        external_account_id=plaid_account_id,
        external_enrollment_id=item_id,
    )

    logger.info(
        f"Created connection {connection.id} for Plaid account "
        f"{plaid_account_id} ({account_name}) with balance {initial_balance}"
    )
    return connection
