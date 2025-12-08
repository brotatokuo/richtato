"""Sync services."""

from typing import Union

from .plaid_sync_service import PlaidSyncService
from .teller_sync_service import TellerSyncService

__all__ = ["TellerSyncService", "PlaidSyncService", "get_sync_service"]


def get_sync_service(provider: str) -> Union[TellerSyncService, PlaidSyncService]:
    """
    Factory function to get the appropriate sync service for a provider.

    Args:
        provider: The provider name ('teller', 'plaid')

    Returns:
        The appropriate sync service instance

    Raises:
        ValueError: If the provider is unknown
    """
    if provider == "teller":
        return TellerSyncService()
    elif provider == "plaid":
        return PlaidSyncService()
    else:
        raise ValueError(f"Unknown provider: {provider}")
