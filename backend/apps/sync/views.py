"""Views for sync API."""

from django.conf import settings
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from decimal import Decimal
import threading

from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from apps.financial_account.services.account_service import AccountService
from apps.sync.repositories.sync_connection_repository import SyncConnectionRepository
from apps.sync.repositories.sync_job_repository import SyncJobRepository
from apps.sync.serializers import (
    SyncConnectionCreateSerializer,
    SyncConnectionSerializer,
    SyncJobSerializer,
)
from apps.sync.services.teller_sync_service import TellerSyncService
from integrations.teller.client import TellerClient
from loguru import logger


class SyncConnectionListCreateAPIView(APIView):
    """List all sync connections or create a new one."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection_repository = SyncConnectionRepository()
        self.account_service = AccountService()
        self.account_repository = FinancialAccountRepository()

    def get(self, request):
        """List all sync connections for the user."""
        connections = self.connection_repository.get_by_user(request.user)
        serializer = SyncConnectionSerializer(connections, many=True)
        return Response({"connections": serializer.data})

    def post(self, request):
        """Create Teller sync connections for all accounts in an enrollment."""
        serializer = SyncConnectionCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_token = serializer.validated_data["access_token"]
            institution_name = serializer.validated_data["institution_name"]
            external_enrollment_id = serializer.validated_data.get(
                "external_enrollment_id", ""
            )
            external_account_id = serializer.validated_data.get("external_account_id")

            # Check if this is an enrollment ID (starts with 'enr_') or no account ID provided
            # In either case, we need to fetch actual accounts from Teller
            is_enrollment_id = (
                external_account_id and external_account_id.startswith("enr_")
            ) or not external_account_id

            if is_enrollment_id:
                # Fetch actual accounts from Teller API
                teller_accounts = self._fetch_teller_accounts(access_token)

                if not teller_accounts:
                    return Response(
                        {"error": "No accounts found in Teller enrollment"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Create a connection for each account
                created_connections = []
                for teller_account in teller_accounts:
                    connection = self._create_connection_for_account(
                        user=request.user,
                        teller_account=teller_account,
                        access_token=access_token,
                        institution_name=institution_name,
                        external_enrollment_id=external_enrollment_id,
                    )
                    if connection:
                        created_connections.append(connection)

                if not created_connections:
                    return Response(
                        {"error": "Failed to create any connections"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                response_serializer = SyncConnectionSerializer(
                    created_connections, many=True
                )
                return Response(
                    {"connections": response_serializer.data},
                    status=status.HTTP_201_CREATED,
                )
            else:
                # Single account ID provided - use original flow
                connection = self._create_single_connection(
                    user=request.user,
                    validated_data=serializer.validated_data,
                )
                response_serializer = SyncConnectionSerializer(connection)
                return Response(
                    response_serializer.data, status=status.HTTP_201_CREATED
                )

        except Exception as e:
            logger.error(f"Error creating sync connection: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _fetch_teller_accounts(self, access_token: str):
        """Fetch accounts from Teller API using the access token."""
        try:
            cert_path = settings.TELLER_CERT_PATH
            key_path = settings.TELLER_KEY_PATH

            if not cert_path or not key_path:
                logger.error("Teller certificate paths not configured")
                return []

            client = TellerClient(
                cert_path=cert_path,
                key_path=key_path,
                access_token=access_token,
            )
            accounts = client.get_accounts()
            logger.info(f"Fetched {len(accounts)} accounts from Teller")
            return accounts
        except Exception as e:
            logger.error(f"Error fetching Teller accounts: {str(e)}")
            return []

    def _create_connection_for_account(
        self,
        user,
        teller_account: dict,
        access_token: str,
        institution_name: str,
        external_enrollment_id: str,
    ):
        """Create a FinancialAccount and SyncConnection for a Teller account."""
        try:
            teller_account_id = teller_account.get("id")
            account_name = teller_account.get("name", "Account")
            account_type = teller_account.get("type", "depository")
            account_subtype = teller_account.get("subtype", "")
            last_four = teller_account.get("last_four", "")

            # Check if connection already exists for this account
            existing = self.connection_repository.get_by_external_account_id(
                user, "teller", teller_account_id
            )
            if existing:
                logger.info(
                    f"Connection already exists for Teller account {teller_account_id}"
                )
                return existing

            # Map Teller account types to our types
            type_mapping = {
                "depository": "checking",
                "credit": "credit_card",
            }
            # Use subtype for more specific mapping
            if account_subtype == "savings":
                mapped_type = "savings"
            elif account_subtype == "checking":
                mapped_type = "checking"
            else:
                mapped_type = type_mapping.get(account_type, "checking")

            # Use balance from the accounts response (already fetched)
            initial_balance = Decimal("0")
            try:
                balances = teller_account.get("balances", {})
                ledger_balance = balances.get("ledger")
                if ledger_balance is not None:
                    initial_balance = Decimal(str(ledger_balance))
                    logger.info(
                        f"Got initial balance for {account_name}: {initial_balance}"
                    )
            except Exception as e:
                logger.warning(f"Could not parse balance for {teller_account_id}: {e}")

            # Create FinancialAccount with initial balance
            financial_account = self.account_service.create_manual_account(
                user=user,
                name=f"{institution_name} {account_name}",
                account_type=mapped_type,
                institution_name=institution_name,
                account_number_last4=last_four,
                initial_balance=initial_balance,
            )
            financial_account.sync_source = "teller"
            # Set is_liability for credit card accounts
            if mapped_type == "credit_card":
                financial_account.is_liability = True
            financial_account.save()

            # Record initial balance in history for net worth tracking
            if initial_balance != Decimal("0"):
                self.account_repository.update_balance(
                    financial_account, initial_balance
                )
                logger.info(
                    f"Recorded initial balance history for account {financial_account.id}"
                )

            # Create SyncConnection
            connection = self.connection_repository.create_connection(
                user=user,
                account=financial_account,
                provider="teller",
                access_token=access_token,
                institution_name=institution_name,
                external_account_id=teller_account_id,
                external_enrollment_id=external_enrollment_id,
            )

            logger.info(
                f"Created connection {connection.id} for Teller account "
                f"{teller_account_id} ({account_name}) with balance {initial_balance}"
            )
            return connection

        except Exception as e:
            logger.error(
                f"Error creating connection for Teller account "
                f"{teller_account.get('id')}: {str(e)}"
            )
            return None

    def _create_single_connection(self, user, validated_data: dict):
        """Create a single connection with explicit account ID."""
        account = None
        if validated_data.get("account_id"):
            account = self.account_service.get_account_by_id(
                validated_data["account_id"], user
            )
            if not account:
                raise ValueError("Account not found")
        else:
            # Auto-create account
            account_name = validated_data.get("account_name")
            account_type = validated_data.get("account_type", "checking")
            institution_name = validated_data["institution_name"]

            type_mapping = {
                "depository": "checking",
                "credit": "credit_card",
                "savings": "savings",
            }
            mapped_type = type_mapping.get(account_type, "checking")

            account = self.account_service.create_manual_account(
                user=user,
                name=account_name or f"{institution_name} Account",
                account_type=mapped_type,
                institution_name=institution_name,
            )
            account.sync_source = "teller"
            # Set is_liability for credit card accounts
            if mapped_type == "credit_card":
                account.is_liability = True
            account.save()

        connection = self.connection_repository.create_connection(
            user=user,
            account=account,
            provider="teller",
            access_token=validated_data["access_token"],
            institution_name=validated_data["institution_name"],
            external_account_id=validated_data["external_account_id"],
            external_enrollment_id=validated_data.get("external_enrollment_id", ""),
        )

        return connection


class SyncConnectionDetailAPIView(APIView):
    """Retrieve or delete a sync connection."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection_repository = SyncConnectionRepository()

    def get(self, request, pk):
        """Get connection details."""
        connection = self.connection_repository.get_by_id(pk)

        if not connection or connection.user != request.user:
            return Response(
                {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = SyncConnectionSerializer(connection)
        return Response(serializer.data)

    def delete(self, request, pk):
        """
        Disconnect/delete connection.

        Query params:
            delete_data: If 'true', also deletes the associated account and all its transactions.
                         If 'false' or omitted, only removes the connection (account becomes manual).
        """
        connection = self.connection_repository.get_by_id(pk)

        if not connection or connection.user != request.user:
            return Response(
                {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if we should also delete the account and its data
        delete_data = request.query_params.get("delete_data", "false").lower() == "true"

        try:
            account = connection.account

            # Delete the connection first
            self.connection_repository.delete_connection(connection)

            if delete_data and account:
                # Delete all transactions for this account
                from apps.transaction.models import Transaction

                Transaction.objects.filter(account=account).delete()

                # Delete the account itself (hard delete, not soft delete)
                account.delete()

                logger.info(
                    f"Deleted connection {pk}, account {account.id}, and all associated data"
                )
            else:
                # Just mark the account as manual if it was synced
                if account and account.sync_source != "manual":
                    account.sync_source = "manual"
                    account.save()
                    logger.info(
                        f"Deleted connection {pk}, converted account {account.id} to manual"
                    )
                else:
                    logger.info(f"Deleted connection {pk}")

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error deleting connection {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SyncTriggerAPIView(APIView):
    """Trigger sync for a connection."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection_repository = SyncConnectionRepository()
        self.sync_service = TellerSyncService()

    def post(self, request, pk):
        """Trigger sync."""
        connection = self.connection_repository.get_by_id(pk)

        if not connection or connection.user != request.user:
            return Response(
                {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
            )

        force_full_sync = request.data.get("full_sync", False)
        if isinstance(force_full_sync, str):
            force_full_sync = force_full_sync.lower() in ["true", "1", "yes"]

        # Create job and start sync in background thread
        def run_sync():
            try:
                self.sync_service.sync_connection(
                    connection, force_full_sync=force_full_sync
                )
            except Exception as e:
                logger.error(f"Background sync error for connection {pk}: {str(e)}")

        thread = threading.Thread(target=run_sync)
        thread.daemon = True
        thread.start()

        # Return immediately with success message
        return Response(
            {
                "success": True,
                "message": "Sync started",
                "accounts_synced": 0,
                "transactions_synced": 0,
                "errors": [],
            }
        )


class SyncJobListAPIView(APIView):
    """List sync jobs for a connection."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection_repository = SyncConnectionRepository()
        self.job_repository = SyncJobRepository()

    def get(self, request, pk):
        """Get sync job history for a connection."""
        connection = self.connection_repository.get_by_id(pk)

        if not connection or connection.user != request.user:
            return Response(
                {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
            )

        jobs = self.job_repository.get_by_connection(connection)
        serializer = SyncJobSerializer(jobs, many=True)
        return Response({"jobs": serializer.data})


class SyncJobProgressAPIView(APIView):
    """Get latest sync job progress for a connection (for polling during sync)."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection_repository = SyncConnectionRepository()
        self.job_repository = SyncJobRepository()

    def get(self, request, pk):
        """Get the latest sync job progress."""
        connection = self.connection_repository.get_by_id(pk)

        if not connection or connection.user != request.user:
            return Response(
                {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get the most recent job for this connection
        jobs = self.job_repository.get_by_connection(connection)
        if not jobs:
            return Response({"job": None})

        latest_job = jobs[0]  # Already ordered by -started_at
        serializer = SyncJobSerializer(latest_job)
        return Response({"job": serializer.data})
