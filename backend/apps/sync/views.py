"""Views for sync API."""

import threading
from decimal import Decimal

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
from apps.sync.services import get_sync_service
from django.conf import settings
from integrations.plaid.client import PlaidClient
from integrations.teller.client import TellerClient
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


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
        """Create sync connections for all accounts in an enrollment."""
        serializer = SyncConnectionCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Detect provider from request (default to teller for backwards compat)
            provider = serializer.validated_data.get("provider", "teller")
            access_token = serializer.validated_data["access_token"]
            institution_name = serializer.validated_data["institution_name"]
            external_enrollment_id = serializer.validated_data.get(
                "external_enrollment_id", ""
            )
            external_account_id = serializer.validated_data.get("external_account_id")

            if provider == "plaid":
                return self._create_plaid_connections(
                    request.user,
                    access_token,
                    institution_name,
                    external_enrollment_id,
                )
            else:
                return self._create_teller_connections(
                    request.user,
                    access_token,
                    institution_name,
                    external_enrollment_id,
                    external_account_id,
                    serializer.validated_data,
                )

        except Exception as e:
            logger.error(f"Error creating sync connection: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _create_teller_connections(
        self,
        user,
        access_token: str,
        institution_name: str,
        external_enrollment_id: str,
        external_account_id: str,
        validated_data: dict,
    ):
        """Create Teller sync connections."""
        # Check if this is an enrollment ID (starts with 'enr_') or no account ID provided
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
                connection = self._create_connection_for_teller_account(
                    user=user,
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
                user=user,
                validated_data=validated_data,
                provider="teller",
            )
            response_serializer = SyncConnectionSerializer(connection)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def _create_plaid_connections(
        self,
        user,
        access_token: str,
        institution_name: str,
        item_id: str,
    ):
        """Create Plaid sync connections for all accounts."""
        try:
            plaid_accounts = self._fetch_plaid_accounts(access_token)

            if not plaid_accounts:
                return Response(
                    {"error": "No accounts found in Plaid item"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            created_connections = []
            for plaid_account in plaid_accounts:
                connection = self._create_connection_for_plaid_account(
                    user=user,
                    plaid_account=plaid_account,
                    access_token=access_token,
                    institution_name=institution_name,
                    item_id=item_id,
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

        except Exception as e:
            logger.error(f"Error creating Plaid connections: {str(e)}")
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

    def _fetch_plaid_accounts(self, access_token: str):
        """Fetch accounts from Plaid API using the access token."""
        try:
            client_id = settings.PLAID_CLIENT_ID
            secret = settings.PLAID_SECRET
            environment = getattr(settings, "PLAID_ENV", "sandbox")

            if not client_id or not secret:
                logger.error("Plaid credentials not configured")
                return []

            client = PlaidClient(
                client_id=client_id,
                secret=secret,
                environment=environment,
                access_token=access_token,
            )
            accounts = client.get_accounts()
            logger.info(f"Fetched {len(accounts)} accounts from Plaid")
            return accounts
        except Exception as e:
            logger.error(f"Error fetching Plaid accounts: {str(e)}")
            return []

    def _create_connection_for_teller_account(
        self,
        user,
        teller_account: dict,
        access_token: str,
        institution_name: str,
        external_enrollment_id: str,
    ):
        """Create a FinancialAccount and SyncConnection for a Teller account."""
        try:
            teller_account_id = teller_account.get("id") or ""
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

    def _create_connection_for_plaid_account(
        self,
        user,
        plaid_account: dict,
        access_token: str,
        institution_name: str,
        item_id: str,
    ):
        """Create a FinancialAccount and SyncConnection for a Plaid account."""
        try:
            plaid_account_id = plaid_account.get("id") or ""
            account_name = plaid_account.get("name", "Account")
            account_type = plaid_account.get("type", "depository")
            account_subtype = plaid_account.get("subtype", "")
            last_four = plaid_account.get("last_four", "")

            # Check if connection already exists for this account
            existing = self.connection_repository.get_by_external_account_id(
                user, "plaid", plaid_account_id
            )
            if existing:
                logger.info(
                    f"Connection already exists for Plaid account {plaid_account_id}"
                )
                return existing

            # Map Plaid account types to our types
            type_mapping = {
                "depository": "checking",
                "credit": "credit_card",
                "loan": "loan",
                "investment": "investment",
            }
            # Use subtype for more specific mapping
            if account_subtype in ("savings", "cd", "money market"):
                mapped_type = "savings"
            elif account_subtype == "checking":
                mapped_type = "checking"
            elif account_subtype == "credit card":
                mapped_type = "credit_card"
            else:
                mapped_type = type_mapping.get(account_type, "checking")

            # Use balance from the accounts response
            initial_balance = Decimal("0")
            try:
                balances = plaid_account.get("balances", {})
                current_balance = balances.get("current") or balances.get("ledger")
                if current_balance is not None:
                    initial_balance = Decimal(str(current_balance))
                    logger.info(
                        f"Got initial balance for {account_name}: {initial_balance}"
                    )
            except Exception as e:
                logger.warning(f"Could not parse balance for {plaid_account_id}: {e}")

            # Create FinancialAccount with initial balance
            financial_account = self.account_service.create_manual_account(
                user=user,
                name=f"{institution_name} {account_name}",
                account_type=mapped_type,
                institution_name=institution_name,
                account_number_last4=last_four,
                initial_balance=initial_balance,
            )
            financial_account.sync_source = "plaid"
            # Set is_liability for credit card and loan accounts
            if mapped_type in ("credit_card", "loan"):
                financial_account.is_liability = True
            financial_account.save()

            # Record initial balance in history
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
                provider="plaid",
                access_token=access_token,
                institution_name=institution_name,
                external_account_id=plaid_account_id,
                external_enrollment_id=item_id,  # Plaid uses item_id
            )

            logger.info(
                f"Created connection {connection.id} for Plaid account "
                f"{plaid_account_id} ({account_name}) with balance {initial_balance}"
            )
            return connection

        except Exception as e:
            logger.error(
                f"Error creating connection for Plaid account "
                f"{plaid_account.get('id')}: {str(e)}"
            )
            return None

    def _create_single_connection(
        self, user, validated_data: dict, provider: str = "teller"
    ):
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
            account.sync_source = provider
            # Set is_liability for credit card accounts
            if mapped_type == "credit_card":
                account.is_liability = True
            account.save()

        connection = self.connection_repository.create_connection(
            user=user,
            account=account,
            provider=provider,
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

        # Get the appropriate sync service based on provider
        try:
            sync_service = get_sync_service(connection.provider)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Create job and start sync in background thread
        def run_sync():
            try:
                sync_service.sync_connection(
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


# ============================================================================
# Plaid-specific endpoints
# ============================================================================


class PlaidLinkTokenAPIView(APIView):
    """Create a Plaid Link token for initializing Plaid Link."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a Link token."""
        try:
            client_id = settings.PLAID_CLIENT_ID
            secret = settings.PLAID_SECRET
            environment = getattr(settings, "PLAID_ENV", "sandbox")

            if not client_id or not secret:
                return Response(
                    {"error": "Plaid is not configured"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            client = PlaidClient(
                client_id=client_id,
                secret=secret,
                environment=environment,
            )

            # Use user ID as the client user ID
            user_id = str(request.user.id)
            redirect_uri = request.data.get("redirect_uri")

            link_token = client.create_link_token(
                user_id=user_id,
                redirect_uri=redirect_uri,
            )

            return Response({"link_token": link_token})

        except Exception as e:
            logger.error(f"Error creating Plaid link token: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PlaidExchangeTokenAPIView(APIView):
    """Exchange a Plaid public token for an access token."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Exchange public token for access token."""
        public_token = request.data.get("public_token")
        institution_name = request.data.get("institution_name", "Bank")

        if not public_token:
            return Response(
                {"error": "public_token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client_id = settings.PLAID_CLIENT_ID
            secret = settings.PLAID_SECRET
            environment = getattr(settings, "PLAID_ENV", "sandbox")

            if not client_id or not secret:
                return Response(
                    {"error": "Plaid is not configured"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            client = PlaidClient(
                client_id=client_id,
                secret=secret,
                environment=environment,
            )

            # Exchange public token for access token
            result = client.exchange_public_token(public_token)
            access_token = result["access_token"]
            item_id = result["item_id"]

            # Now create connections for all accounts
            connection_repository = SyncConnectionRepository()
            account_service = AccountService()
            account_repository = FinancialAccountRepository()

            # Create a temporary client with access token to fetch accounts
            client_with_token = PlaidClient(
                client_id=client_id,
                secret=secret,
                environment=environment,
                access_token=access_token,
            )

            plaid_accounts = client_with_token.get_accounts()

            if not plaid_accounts:
                return Response(
                    {"error": "No accounts found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            created_connections = []
            for plaid_account in plaid_accounts:
                plaid_account_id = plaid_account.get("id")
                account_name = plaid_account.get("name", "Account")
                account_type = plaid_account.get("type", "depository")
                account_subtype = plaid_account.get("subtype", "")
                last_four = plaid_account.get("last_four", "")

                # Check if connection already exists
                existing = connection_repository.get_by_external_account_id(
                    request.user, "plaid", plaid_account_id
                )
                if existing:
                    created_connections.append(existing)
                    continue

                # Map account types
                type_mapping = {
                    "depository": "checking",
                    "credit": "credit_card",
                    "loan": "loan",
                    "investment": "investment",
                }
                if account_subtype in ("savings", "cd", "money market"):
                    mapped_type = "savings"
                elif account_subtype == "checking":
                    mapped_type = "checking"
                elif account_subtype == "credit card":
                    mapped_type = "credit_card"
                else:
                    mapped_type = type_mapping.get(account_type, "checking")

                # Get initial balance
                initial_balance = Decimal("0")
                try:
                    balances = plaid_account.get("balances", {})
                    current = balances.get("current") or balances.get("ledger")
                    if current is not None:
                        initial_balance = Decimal(str(current))
                except Exception:
                    pass

                # Create FinancialAccount
                financial_account = account_service.create_manual_account(
                    user=request.user,
                    name=f"{institution_name} {account_name}",
                    account_type=mapped_type,
                    institution_name=institution_name,
                    account_number_last4=last_four,
                    initial_balance=initial_balance,
                )
                financial_account.sync_source = "plaid"
                if mapped_type in ("credit_card", "loan"):
                    financial_account.is_liability = True
                financial_account.save()

                if initial_balance != Decimal("0"):
                    account_repository.update_balance(
                        financial_account, initial_balance
                    )

                # Create SyncConnection
                connection = connection_repository.create_connection(
                    user=request.user,
                    account=financial_account,
                    provider="plaid",
                    access_token=access_token,
                    institution_name=institution_name,
                    external_account_id=plaid_account_id,
                    external_enrollment_id=item_id,
                )
                created_connections.append(connection)

            serializer = SyncConnectionSerializer(created_connections, many=True)
            return Response(
                {"connections": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error exchanging Plaid token: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# Sync Status endpoints (for frontend polling)
# ============================================================================


class SyncStatusAPIView(APIView):
    """Get current sync status for frontend polling."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get the current sync status for the user."""
        try:
            from apps.sync.models import UserSyncStatus

            logger.debug(f"SyncStatusAPIView.get called for user {request.user.id}")
            status_obj = UserSyncStatus.objects.filter(user=request.user).first()

            if not status_obj:
                return Response(
                    {
                        "is_syncing": False,
                        "new_transaction_count": 0,
                        "last_sync": None,
                    }
                )

            return Response(
                {
                    "is_syncing": status_obj.is_syncing,
                    "new_transaction_count": status_obj.new_transaction_count,
                    "last_sync": status_obj.last_sync_completed,
                    "last_error": status_obj.last_error or "",
                }
            )
        except Exception as e:
            logger.error(f"SyncStatusAPIView.get error: {e}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Trigger background sync for all user connections."""
        try:
            from apps.sync.models import SyncConnection
            from apps.sync.services.background_sync_service import BackgroundSyncService

            logger.info(f"SyncStatusAPIView.post called for user {request.user.id}")

            # Check if user has any active connections
            has_connections = SyncConnection.objects.filter(
                user=request.user, status="active"
            ).exists()

            if not has_connections:
                logger.info(f"No active connections for user {request.user.id}")
                return Response(
                    {
                        "status": "no_connections",
                        "message": "No active connections to sync",
                    },
                    status=status.HTTP_200_OK,
                )

            # Trigger background sync
            logger.info(f"Triggering sync for user {request.user.id}")
            BackgroundSyncService.trigger_user_sync(request.user.id)

            return Response(
                {
                    "status": "sync_started",
                    "message": "Sync started for all connections",
                }
            )
        except Exception as e:
            logger.error(f"SyncStatusAPIView.post error: {e}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request):
        """Clear new transaction count (user has seen them)."""
        try:
            from apps.sync.models import UserSyncStatus

            UserSyncStatus.objects.filter(user=request.user).update(
                new_transaction_count=0
            )
            return Response({"status": "cleared"})
        except Exception as e:
            logger.error(f"SyncStatusAPIView.delete error: {e}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserSyncJobsAPIView(APIView):
    """List all sync jobs for the current user across all connections."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get sync job history for the user (last 20 jobs)."""
        from apps.sync.models import SyncJob

        # Get all jobs for the user's connections, ordered by most recent
        jobs = (
            SyncJob.objects.filter(connection__user=request.user)
            .select_related("connection")
            .order_by("-started_at")[:20]
        )

        # Serialize with connection info
        jobs_data = []
        for job in jobs:
            jobs_data.append(
                {
                    "id": job.id,
                    "connection_id": job.connection.id,
                    "institution_name": job.connection.institution_name,
                    "provider": job.connection.provider,
                    "status": job.status,
                    "started_at": job.started_at.isoformat()
                    if job.started_at
                    else None,
                    "completed_at": (
                        job.completed_at.isoformat() if job.completed_at else None
                    ),
                    "transactions_synced": job.transactions_synced,
                    "transactions_skipped": job.transactions_skipped,
                    "is_full_sync": job.is_full_sync,
                    "errors": job.errors or [],
                    "duration_seconds": (
                        job.duration.total_seconds() if job.completed_at else None
                    ),
                }
            )

        return Response({"jobs": jobs_data})


class CronSyncAPIView(APIView):
    """Endpoint for Render Cron Job to trigger daily syncs."""

    # No authentication - uses secret key instead
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        """Trigger sync for all active connections."""
        from apps.sync.models import SyncConnection
        from apps.sync.services import get_sync_service

        # Verify secret key
        key = request.GET.get("key")
        cron_secret = getattr(settings, "CRON_SECRET_KEY", None)

        if not cron_secret or key != cron_secret:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        # Get all active connections that are stale (not synced in 20 hours)
        connections = SyncConnection.objects.filter(status="active")
        synced_count = 0
        errors = []

        for conn in connections:
            if conn.is_stale(hours=20):
                try:
                    logger.info(
                        f"Cron sync: Syncing connection {conn.id} ({conn.institution_name}) via {conn.provider}"
                    )
                    sync_service = get_sync_service(conn.provider)
                    sync_service.sync_connection(conn)
                    synced_count += 1
                except Exception as e:
                    logger.error(f"Cron sync error for connection {conn.id}: {e}")
                    errors.append(f"Connection {conn.id}: {str(e)}")

        logger.info(f"Cron sync completed: {synced_count} connections synced")

        return Response(
            {
                "status": "completed",
                "connections_synced": synced_count,
                "errors": errors,
            }
        )
