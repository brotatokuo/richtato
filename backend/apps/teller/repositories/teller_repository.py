"""Repository for Teller connection data access."""

from typing import List, Optional

from apps.teller.models import TellerConnection
from apps.richtato_user.models import User


class TellerRepository:
    """Repository for Teller connection data access - ORM layer only."""

    def get_by_id(self, connection_id: int) -> Optional[TellerConnection]:
        """Get a Teller connection by ID."""
        try:
            return TellerConnection.objects.get(id=connection_id)
        except TellerConnection.DoesNotExist:
            return None

    def get_by_user(self, user: User) -> List[TellerConnection]:
        """Get all Teller connections for a user."""
        return list(TellerConnection.objects.filter(user=user).order_by("-created_at"))

    def get_active_by_user(self, user: User) -> List[TellerConnection]:
        """Get active Teller connections for a user."""
        return list(
            TellerConnection.objects.filter(user=user, status="active").order_by(
                "-created_at"
            )
        )

    def get_by_teller_account_id(
        self, user: User, teller_account_id: str
    ) -> Optional[TellerConnection]:
        """Get a connection by Teller account ID and user."""
        try:
            return TellerConnection.objects.get(
                user=user, teller_account_id=teller_account_id
            )
        except TellerConnection.DoesNotExist:
            return None

    def create(
        self,
        user: User,
        access_token: str,
        teller_account_id: str,
        institution_name: str,
        account_name: str,
        enrollment_id: str = "",
        account_type: str = "",
    ) -> TellerConnection:
        """Create a new Teller connection."""
        connection = TellerConnection.objects.create(
            user=user,
            access_token=access_token,
            teller_account_id=teller_account_id,
            institution_name=institution_name,
            account_name=account_name,
            enrollment_id=enrollment_id,
            account_type=account_type,
            status="active",
        )
        return connection

    def update(self, connection: TellerConnection, **data) -> TellerConnection:
        """Update a Teller connection."""
        for key, value in data.items():
            setattr(connection, key, value)
        connection.save()
        return connection

    def delete(self, connection: TellerConnection) -> None:
        """Delete a Teller connection."""
        connection.delete()

    def disconnect(self, connection: TellerConnection) -> TellerConnection:
        """Mark a connection as disconnected."""
        connection.disconnect()
        return connection
