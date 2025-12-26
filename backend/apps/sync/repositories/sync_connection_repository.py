"""Repository for SyncConnection model."""

from typing import List, Optional

from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.sync.models import SyncConnection


class SyncConnectionRepository:
    """Repository for sync connection data access."""

    def get_by_id(self, connection_id: int) -> Optional[SyncConnection]:
        """Get connection by ID."""
        try:
            return SyncConnection.objects.select_related("user", "account").get(
                id=connection_id
            )
        except SyncConnection.DoesNotExist:
            return None

    def get_by_user(
        self, user: User, active_only: bool = False
    ) -> List[SyncConnection]:
        """Get all sync connections for a user."""
        queryset = SyncConnection.objects.filter(user=user).select_related("account")
        if active_only:
            queryset = queryset.filter(status="active")
        return list(queryset.all())

    def get_by_provider(
        self, user: User, provider: str, active_only: bool = True
    ) -> List[SyncConnection]:
        """Get connections by provider."""
        queryset = SyncConnection.objects.filter(
            user=user, provider=provider
        ).select_related("account")
        if active_only:
            queryset = queryset.filter(status="active")
        return list(queryset.all())

    def get_by_external_account_id(
        self, user: User, provider: str, external_account_id: str
    ) -> Optional[SyncConnection]:
        """Get connection by external account ID."""
        try:
            return SyncConnection.objects.get(
                user=user, provider=provider, external_account_id=external_account_id
            )
        except SyncConnection.DoesNotExist:
            return None

    def create_connection(
        self,
        user: User,
        account: FinancialAccount,
        provider: str,
        access_token: str,
        institution_name: str,
        external_account_id: str,
        external_enrollment_id: str = "",
        sync_frequency: str = "manual",
    ) -> SyncConnection:
        """Create a new sync connection."""
        connection = SyncConnection.objects.create(
            user=user,
            account=account,
            provider=provider,
            access_token=access_token,
            institution_name=institution_name,
            external_account_id=external_account_id,
            external_enrollment_id=external_enrollment_id,
            sync_frequency=sync_frequency,
        )
        return connection

    def update_connection(self, connection: SyncConnection, **kwargs) -> SyncConnection:
        """Update connection fields."""
        for key, value in kwargs.items():
            if hasattr(connection, key):
                setattr(connection, key, value)
        connection.save()
        return connection

    def delete_connection(self, connection: SyncConnection) -> None:
        """Mark connection as disconnected."""
        connection.status = "disconnected"
        connection.save()

    def hard_delete_connection(self, connection: SyncConnection) -> None:
        """Permanently delete a connection."""
        connection.delete()
