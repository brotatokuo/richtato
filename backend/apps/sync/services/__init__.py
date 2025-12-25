"""Sync services."""

from .plaid_sync_service import PlaidSyncService

__all__ = ["PlaidSyncService", "get_sync_service"]


def get_sync_service(provider: str) -> PlaidSyncService:
    """
    Factory function to get the appropriate sync service for a provider.

    Args:
        provider: The provider name ('plaid')

    Returns:
        The appropriate sync service instance

    Raises:
        ValueError: If the provider is unknown
    """
    if provider == "plaid":
        return PlaidSyncService()
    else:
        raise ValueError(f"Unknown provider: {provider}")
