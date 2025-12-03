"""Teller connection service for business logic."""

from typing import Dict, List, Optional

from apps.richtato_user.models import User
from apps.teller.models import TellerConnection
from apps.teller.repositories.teller_repository import TellerRepository
from django.conf import settings
from integrations.teller.client import TellerClient
from loguru import logger


class TellerService:
    """Service for Teller connection business logic."""

    def __init__(self):
        self.repository = TellerRepository()

    def _get_teller_client(self, access_token: str) -> TellerClient:
        """
        Create a TellerClient instance with the given access token.

        Args:
            access_token: Teller access token

        Returns:
            Initialized TellerClient
        """
        cert_path = settings.TELLER_CERT_PATH
        key_path = settings.TELLER_KEY_PATH

        if not cert_path or not key_path:
            raise ValueError("Teller certificate paths not configured in settings")

        return TellerClient(
            cert_path=cert_path,
            key_path=key_path,
            access_token=access_token,
        )

    def get_connections_for_user(self, user: User) -> List[TellerConnection]:
        """Get all Teller connections for a user."""
        return self.repository.get_by_user(user)

    def get_active_connections_for_user(self, user: User) -> List[TellerConnection]:
        """Get active Teller connections for a user."""
        return self.repository.get_active_by_user(user)

    def get_connection_by_id(
        self, connection_id: int, user: User
    ) -> Optional[TellerConnection]:
        """Get a specific Teller connection by ID, ensuring it belongs to the user."""
        connection = self.repository.get_by_id(connection_id)
        if connection and connection.user == user:
            return connection
        return None

    def create_connection(
        self,
        user: User,
        access_token: str,
        teller_account_id: str,
        institution_name: str,
        account_name: str,
        enrollment_id: str = "",
        account_type: str = "",
    ) -> TellerConnection:
        """
        Create a new Teller connection.

        Args:
            user: The user creating the connection
            access_token: Teller access token
            teller_account_id: Teller account ID
            institution_name: Bank/institution name
            account_name: Account name
            enrollment_id: Optional enrollment ID
            account_type: Optional account type

        Returns:
            Created TellerConnection instance
        """
        # Check if connection already exists
        existing = self.repository.get_by_teller_account_id(user, teller_account_id)
        if existing:
            logger.info(
                f"Connection already exists for user {user.username} "
                f"and account {teller_account_id}"
            )
            # Update existing connection instead
            return self.repository.update(
                existing,
                access_token=access_token,
                institution_name=institution_name,
                account_name=account_name,
                enrollment_id=enrollment_id,
                account_type=account_type,
                status="active",
            )

        connection = self.repository.create(
            user=user,
            access_token=access_token,
            teller_account_id=teller_account_id,
            institution_name=institution_name,
            account_name=account_name,
            enrollment_id=enrollment_id,
            account_type=account_type,
        )
        logger.info(
            f"Created Teller connection {connection.id} for user {user.username}"
        )
        return connection

    def create_connections_from_enrollment(
        self,
        user: User,
        access_token: str,
        enrollment_id: str,
        institution_name: str,
    ) -> List[TellerConnection]:
        """
        Fetch accounts from Teller and create connections for each account.

        Args:
            user: The user creating the connection
            access_token: Teller access token
            enrollment_id: Teller enrollment ID
            institution_name: Bank/institution name

        Returns:
            List of created TellerConnection instances
        """
        try:
            # Fetch accounts from Teller
            client = self._get_teller_client(access_token)
            accounts = client.get_accounts()

            logger.info(
                f"Fetched {len(accounts)} accounts from Teller for "
                f"user {user.username}, enrollment {enrollment_id}"
            )

            if not accounts:
                raise ValueError("No accounts found for this enrollment")

            created_connections = []

            # Create a connection for each account
            for account in accounts:
                account_id = account.get("id")
                account_name = account.get("name", "")
                account_type = account.get("type", "")

                # Check if connection already exists
                existing = self.repository.get_by_teller_account_id(user, account_id)
                if existing:
                    logger.info(
                        f"Connection already exists for account {account_id}, updating"
                    )
                    # Update existing connection
                    updated = self.repository.update(
                        existing,
                        access_token=access_token,
                        institution_name=institution_name,
                        account_name=account_name or account_type or "Account",
                        enrollment_id=enrollment_id,
                        account_type=account_type,
                        status="active",
                    )
                    created_connections.append(updated)
                else:
                    # Create new connection
                    connection = self.repository.create(
                        user=user,
                        access_token=access_token,
                        teller_account_id=account_id,
                        institution_name=institution_name,
                        account_name=account_name or account_type or "Account",
                        enrollment_id=enrollment_id,
                        account_type=account_type,
                    )
                    logger.info(
                        f"Created Teller connection {connection.id} for account {account_id}"
                    )
                    created_connections.append(connection)

            return created_connections

        except Exception as e:
            logger.error(f"Error creating connections from enrollment: {str(e)}")
            raise

    def disconnect_connection(
        self, connection_id: int, user: User
    ) -> Optional[TellerConnection]:
        """
        Disconnect (soft delete) a Teller connection.

        Args:
            connection_id: ID of the connection to disconnect
            user: The user making the request

        Returns:
            Updated TellerConnection if successful, None otherwise
        """
        connection = self.get_connection_by_id(connection_id, user)
        if not connection:
            logger.warning(
                f"Connection {connection_id} not found for user {user.username}"
            )
            return None

        disconnected = self.repository.disconnect(connection)
        logger.info(
            f"Disconnected Teller connection {connection_id} for user {user.username}"
        )
        return disconnected

    def delete_connection(self, connection_id: int, user: User) -> bool:
        """
        Permanently delete a Teller connection.

        Args:
            connection_id: ID of the connection to delete
            user: The user making the request

        Returns:
            True if deleted successfully, False otherwise
        """
        connection = self.get_connection_by_id(connection_id, user)
        if not connection:
            logger.warning(
                f"Connection {connection_id} not found for user {user.username}"
            )
            return False

        self.repository.delete(connection)
        logger.info(
            f"Deleted Teller connection {connection_id} for user {user.username}"
        )
        return True
