"""Views for financial accounts API."""

from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.financial_account.serializers import (
    FinancialAccountCreateSerializer,
    FinancialAccountSerializer,
    FinancialAccountUpdateSerializer,
)
from apps.financial_account.services.account_balance_service import (
    AccountBalanceService,
)
from apps.financial_account.services.account_service import AccountService
from apps.financial_account.services.bank_agent_config_service import BankAgentConfigOptions, BankAgentConfigService
from apps.financial_account.services.bank_agent_setup_export_service import BankAgentSetupExportService
from apps.financial_account.services.bank_sync_setup_service import BankSyncSetupService
from apps.financial_account.services.google_drive_activation_service import GoogleDriveActivationService
from apps.financial_account.services.google_drive_service import GoogleDriveError, GoogleDriveService
from apps.financial_account.services.statement_file_service import (
    StatementFileService,
)
from apps.financial_account.services.statement_import_service import (
    StatementImportService,
)
from apps.financial_account.services.storage_scanner_service import (
    StorageScannerService,
    parser_key_for_account,
)

SENSITIVE_ACCOUNT_FIELDS = {"agent_activity_url"}


def _redact_account_payload(payload):
    """Return a log-safe copy of an account mutation payload."""
    return {key: ("[redacted]" if key in SENSITIVE_ACCOUNT_FIELDS else value) for key, value in payload.items()}


class FinancialAccountListCreateAPIView(APIView):
    """List all accounts or create a new manual account."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()

    def get(self, request):
        """List all financial accounts for the user."""
        from apps.household.scope import get_scope_user_ids

        active_only = request.query_params.get("active_only", "true").lower() == "true"
        account_type = request.query_params.get("type")

        scope = request.query_params.get("scope", "personal")
        user_ids = get_scope_user_ids(request)

        if scope == "household" and len(user_ids) > 1:
            accounts = self.account_service.get_household_accounts(
                user_ids,
                active_only=active_only,
            )
        elif account_type:
            accounts = self.account_service.get_accounts_by_type(request.user, account_type)
        else:
            accounts = self.account_service.get_user_accounts(request.user, active_only=active_only)

        serializer = FinancialAccountSerializer(accounts, many=True)
        return Response({"accounts": serializer.data, "rows": serializer.data})

    def post(self, request):
        """Create a new manual financial account."""
        serializer = FinancialAccountCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = self.account_service.create_manual_account(user=request.user, **serializer.validated_data)

            response_serializer = FinancialAccountSerializer(account)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating manual account: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinancialAccountDetailAPIView(APIView):
    """Retrieve, update or delete a financial account."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()

    def get(self, request, pk):
        """Get account details."""
        account = self.account_service.get_account_by_id(pk, request.user)

        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = FinancialAccountSerializer(account)
        return Response(serializer.data)

    def patch(self, request, pk):
        """Update account."""
        account = self.account_service.get_account_by_id(pk, request.user)

        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        logger.info(
            "Account PATCH request",
            account_id=pk,
            user_id=request.user.id,
            payload=_redact_account_payload(dict(request.data)),
        )

        serializer = FinancialAccountUpdateSerializer(
            data=request.data,
            context={"account": account},
        )
        if not serializer.is_valid():
            logger.warning(
                "Account PATCH validation failed",
                account_id=pk,
                user_id=request.user.id,
                errors=serializer.errors,
                payload=_redact_account_payload(dict(request.data)),
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            logger.info(
                "Account PATCH validated",
                account_id=pk,
                validated_data=_redact_account_payload(
                    {key: str(value) for key, value in serializer.validated_data.items()}
                ),
            )
            updated_account = self.account_service.update_account(account, **serializer.validated_data)
            updated_account.refresh_from_db()
            response_serializer = FinancialAccountSerializer(updated_account)
            logger.info(
                "Account PATCH succeeded",
                account_id=pk,
                balance=str(updated_account.balance),
                opening_balance=response_serializer.data.get("opening_balance"),
                opening_balance_date=response_serializer.data.get("opening_balance_date"),
            )
            return Response(response_serializer.data)

        except Exception as e:
            logger.exception(f"Error updating account {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        """Delete (deactivate) account."""
        account = self.account_service.get_account_by_id(pk, request.user)

        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            self.account_service.delete_account(account)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error deleting account {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountBalanceHistoryAPIView(APIView):
    """Get balance history for an account."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()
        self.balance_service = AccountBalanceService()

    def get(self, request, pk):
        """Get balance history."""
        account = self.account_service.get_account_by_id(pk, request.user)

        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            trend_data = self.balance_service.get_balance_trend(account)
            return Response(trend_data)

        except Exception as e:
            logger.error(f"Error getting balance history for account {pk}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountSummaryAPIView(APIView):
    """Get summary of all user accounts."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()

    def get(self, request):
        """Get account summary."""
        try:
            summary = self.account_service.get_account_summary(request.user)
            return Response(summary)

        except Exception as e:
            logger.error(f"Error getting account summary: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountFieldChoicesAPIView(APIView):
    """Get field choices for account forms."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get available account types and entities."""
        from apps.financial_account.institutions.registry import get_institution_field_choices

        return Response(get_institution_field_choices())


class BankAgentConfigAPIView(APIView):
    """Return generated host bank-agent config for the authenticated user's accounts."""

    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_service = BankAgentConfigService()

    def get(self, request):
        options = BankAgentConfigOptions(
            nickname=request.query_params.get("nickname", "personal"),
            include_all_supported=request.query_params.get("include") == "all-supported",
        )

        return Response(self.config_service.build_for_user(request.user, options), status=status.HTTP_200_OK)


class BankAgentSetupExportAPIView(APIView):
    """Download a host bank-agent setup YAML file with credentials and login config."""

    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.export_service = BankAgentSetupExportService()

    def get(self, request):
        include_credentials = request.query_params.get("include_credentials", "1") != "0"
        yaml_text = self.export_service.build_yaml_for_user(
            request.user,
            include_credentials=include_credentials,
            include_all_supported=request.query_params.get("include") == "all-supported",
            nickname=request.query_params.get("nickname", "personal"),
        )
        response = HttpResponse(yaml_text, content_type="text/yaml; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="richtato-bank-agent-setup.yml"'
        return response


class BankSyncSetupAPIView(APIView):
    """Return per-account sync settings and generated bank-agent config for Setup → Sync."""

    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_service = BankSyncSetupService()

    def get(self, request):
        return Response(self.setup_service.build_for_user(request.user), status=status.HTTP_200_OK)


class GoogleDriveStatusAPIView(APIView):
    """Return Google Drive statement storage connection status."""

    authentication_classes = [SessionAuthentication, TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.activation_service = GoogleDriveActivationService()

    def get(self, request):
        return Response(self.activation_service.status(request.user), status=status.HTTP_200_OK)


class GoogleDriveOAuthStartAPIView(APIView):
    """Start Google OAuth for statement storage."""

    authentication_classes = [SessionAuthentication, TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drive_service = GoogleDriveService()

    def post(self, request):
        try:
            auth_url, state = self.drive_service.build_authorization_url(request)
        except GoogleDriveError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        request.session["google_drive_oauth_state"] = state
        return Response({"auth_url": auth_url}, status=status.HTTP_200_OK)


class GoogleDriveOAuthCallbackAPIView(APIView):
    """Handle Google OAuth callback and redirect back to setup."""

    authentication_classes = [SessionAuthentication, TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drive_service = GoogleDriveService()

    def get(self, request):
        frontend_url = settings.FRONTEND_URL.rstrip("/") + "/setup"
        callback_params = {"tab": "statements"}
        expected_state = request.session.get("google_drive_oauth_state")
        received_state = request.query_params.get("state")
        if expected_state and received_state != expected_state:
            return redirect(f"{frontend_url}?{urlencode({**callback_params, 'drive_error': 'Invalid OAuth state'})}")

        code = request.query_params.get("code")
        if not code:
            message = request.query_params.get("error") or "Missing OAuth code"
            return redirect(f"{frontend_url}?{urlencode({**callback_params, 'drive_error': message})}")

        try:
            self.drive_service.exchange_code(user=request.user, code=code, request=request)
        except GoogleDriveError as exc:
            return redirect(f"{frontend_url}?{urlencode({**callback_params, 'drive_error': str(exc)})}")

        request.session.pop("google_drive_oauth_state", None)
        return redirect(f"{frontend_url}?{urlencode({**callback_params, 'drive': 'connected'})}")


class GoogleDrivePickerTokenAPIView(APIView):
    """Return a short-lived access token for Google Drive Picker."""

    authentication_classes = [SessionAuthentication, TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drive_service = GoogleDriveService()

    def get(self, request):
        connection = getattr(request.user, "google_drive_connection", None)
        if not connection or not connection.refresh_token_encrypted:
            return Response({"error": "Google Drive is not connected"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response(self.drive_service.get_picker_token(connection), status=status.HTTP_200_OK)
        except GoogleDriveError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class GoogleDriveActivateAPIView(APIView):
    """Activate a Drive folder as the statement root."""

    authentication_classes = [SessionAuthentication, TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.activation_service = GoogleDriveActivationService()

    def post(self, request):
        folder_id = request.data.get("folder_id")
        if not folder_id:
            return Response({"error": "folder_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        adopt_existing = bool(request.data.get("adopt_existing"))
        try:
            result = self.activation_service.activate(
                request.user,
                root_folder_id=folder_id,
                root_folder_name=request.data.get("folder_name", ""),
                adopt_existing=adopt_existing,
                scan_after_adopt=adopt_existing,
            )
        except GoogleDriveError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": self.activation_service.status(request.user),
                "account_folders_created": result.account_folders_created,
                "account_folders_adopted": result.account_folders_adopted,
                "unmatched_drive_folders": result.unmatched_drive_folders,
                "scan_summary": result.scan_summary,
                "errors": result.errors,
            },
            status=status.HTTP_200_OK,
        )


class GoogleDriveAdoptPreviewAPIView(APIView):
    """Preview adopting an existing Drive root with Richtato-style account folders."""

    authentication_classes = [SessionAuthentication, TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.activation_service = GoogleDriveActivationService()

    def post(self, request):
        folder_id = request.data.get("folder_id")
        if not folder_id:
            return Response({"error": "folder_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            preview = self.activation_service.preview_adopt_existing(request.user, root_folder_id=folder_id)
        except GoogleDriveError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "root_folder_id": preview.root_folder_id,
                "root_folder_name": preview.root_folder_name,
                "adopted": preview.adopted,
                "would_create": preview.would_create,
                "unmatched": preview.unmatched,
                "statement_file_counts": preview.statement_file_counts,
                "errors": preview.errors,
            },
            status=status.HTTP_200_OK,
        )


class GoogleDriveDeactivateAPIView(APIView):
    """Unlink an active Drive statement root and clear account storage URIs."""

    authentication_classes = [SessionAuthentication, TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.activation_service = GoogleDriveActivationService()

    def post(self, request):
        try:
            result = self.activation_service.deactivate(request.user)
        except GoogleDriveError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "status": self.activation_service.status(request.user),
                "account_folders_removed": result.account_folders_removed,
                "errors": result.errors,
            },
            status=status.HTTP_200_OK,
        )


class GoogleDriveDisconnectAPIView(APIView):
    """Disconnect inactive Google Drive OAuth credentials."""

    authentication_classes = [SessionAuthentication, TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.activation_service = GoogleDriveActivationService()

    def post(self, request):
        try:
            self.activation_service.disconnect_if_inactive(request.user)
        except GoogleDriveError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.activation_service.status(request.user), status=status.HTTP_200_OK)


class GoogleDriveSyncFoldersAPIView(APIView):
    """Create Drive folders for any active accounts that are missing one."""

    authentication_classes = [SessionAuthentication, TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.activation_service = GoogleDriveActivationService()

    def post(self, request):
        try:
            result = self.activation_service.sync_missing_folders(request.user)
        except GoogleDriveError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "status": self.activation_service.status(request.user),
                "account_folders_created": result.account_folders_created,
                "errors": result.errors,
            },
            status=status.HTTP_200_OK,
        )


class AccountScanStorageAPIView(APIView):
    """Scan an account's storage URI for new statement files and auto-import them."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()
        self.scanner = StorageScannerService()

    def post(self, request, pk):
        account = self.account_service.get_account_by_id(pk, request.user)
        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        result = self.scanner.scan_account(account.id)
        return Response(
            {
                "accounts_scanned": result.accounts_scanned,
                "files_seen": result.files_seen,
                "files_imported": result.files_imported,
                "files_skipped": result.files_skipped,
                "files_failed": result.files_failed,
                "files_removed": result.files_removed,
                "outcomes": [
                    {
                        "relative_path": o.relative_path,
                        "status": o.status,
                        "detail": o.detail,
                        "imported_count": o.imported_count,
                    }
                    for o in result.outcomes
                ],
            },
            status=status.HTTP_200_OK,
        )


class AccountTransactionsAPIView(APIView):
    """Get transactions for a specific account."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()
        from apps.transaction.services.transaction_service import TransactionService

        self.transaction_service = TransactionService()

    def get(self, request, pk):
        """Get paginated transactions for an account."""
        account = self.account_service.get_account_by_id(pk, request.user)

        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        queryset = self.transaction_service.get_user_transactions(user=request.user, account=account)
        total = queryset.count()

        start = (page - 1) * page_size
        end = start + page_size
        transactions = queryset[start:end]

        columns = [
            {"field": "id", "title": "ID"},
            {"field": "date", "title": "Date"},
            {"field": "description", "title": "Description"},
            {"field": "amount", "title": "Amount"},
            {"field": "transaction_type", "title": "Type"},
        ]

        rows = [
            {
                "id": t.id,
                "date": t.date.isoformat() if t.date else None,
                "description": t.description or "",
                "amount": str(t.amount),
                "transaction_type": t.transaction_type,
            }
            for t in transactions
        ]

        return Response(
            {
                "columns": columns,
                "rows": rows,
                "page": page,
                "page_size": page_size,
                "total": total,
            }
        )

    def patch(self, request, pk):
        """Update a transaction."""
        account = self.account_service.get_account_by_id(pk, request.user)
        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        transaction_id = request.data.get("id")
        if not transaction_id:
            return Response({"error": "Transaction ID required"}, status=status.HTTP_400_BAD_REQUEST)

        transaction = self.transaction_service.get_transaction_by_id(transaction_id, request.user)
        if not transaction or transaction.account_id != account.id:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

        update_kwargs = {}
        if "amount" in request.data:
            update_kwargs["amount"] = request.data["amount"]
        if "date" in request.data:
            update_kwargs["date"] = request.data["date"]
        transaction = self.transaction_service.update_transaction(transaction, **update_kwargs)
        return Response(
            {
                "id": transaction.id,
                "amount": str(transaction.amount),
                "date": str(transaction.date),
            }
        )

    def delete(self, request, pk):
        """Delete a transaction."""
        account = self.account_service.get_account_by_id(pk, request.user)
        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        transaction_id = request.data.get("id")
        if not transaction_id:
            return Response({"error": "Transaction ID required"}, status=status.HTTP_400_BAD_REQUEST)

        transaction = self.transaction_service.get_transaction_by_id(transaction_id, request.user)
        if not transaction or transaction.account_id != account.id:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

        self.transaction_service.delete_transaction(transaction)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountBalanceUpdateAPIView(APIView):
    """Set the absolute balance for an account on a given date.

    This writes directly to FinancialAccount.balance and AccountBalanceHistory
    without creating a Transaction. Use when the user wants to reconcile or
    snapshot the account balance (e.g. "my balance is $5,200 today").
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()
        self.balance_service = AccountBalanceService()

    def post(self, request):
        """Set the account balance to the given amount on the given date."""
        from datetime import date as date_type
        from decimal import Decimal

        account_id = request.data.get("account")
        balance = request.data.get("balance")
        balance_date = request.data.get("date")

        if not all([account_id, balance is not None, balance_date]):
            return Response(
                {"error": "account, balance, and date are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account = self.account_service.get_account_by_id(account_id, request.user)
        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            balance_decimal = Decimal(str(balance))
        except Exception:
            return Response(
                {"error": "Invalid balance value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parsed_balance_date = date_type.fromisoformat(str(balance_date))
        except ValueError:
            return Response(
                {"error": "Invalid date format (use YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_balance = account.balance
        updated_account = self.balance_service.set_balance_snapshot(
            account=account,
            new_balance=balance_decimal,
            balance_date=parsed_balance_date,
        )

        return Response(
            {
                "balance": str(updated_account.balance),
                "date": str(parsed_balance_date),
                "previous_balance": str(old_balance),
                "adjustment": str(updated_account.balance - old_balance),
            },
            status=status.HTTP_200_OK,
        )


class CardAccountListAPIView(APIView):
    """List credit card accounts (for backward compatibility with card-accounts endpoint)."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()

    def get(self, request):
        """List all credit card accounts for the user."""
        accounts = self.account_service.get_accounts_by_type(request.user, "credit_card")
        serializer = FinancialAccountSerializer(accounts, many=True)
        # Return in rows format for backward compatibility
        return Response({"rows": serializer.data})


class CardAccountFieldChoicesAPIView(APIView):
    """Get field choices for credit card accounts (for backward compatibility)."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get available card account choices."""
        from apps.financial_account.models import FinancialAccount

        # Get credit card accounts for the user
        accounts = FinancialAccount.objects.filter(
            user=request.user,
            account_type="credit_card",
            is_active=True,
        )

        account_choices = [{"value": acc.id, "label": acc.name} for acc in accounts]

        return Response({"account": account_choices})


class CSVStatementImportAPIView(APIView):
    """Import transactions from a CSV statement file.

    Deprecated: prefer ``POST /import-statement/`` with ``institution=generic``.
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()
        self.statement_service = StatementImportService()

    def post(self, request):
        """Import a CSV statement into an account.

        Expects multipart form data:
        - file: CSV file
        - account: account ID
        - ending_balance: optional statement ending balance
        - ending_date: optional date for ending balance (YYYY-MM-DD)
        """
        from datetime import date as date_type
        from decimal import Decimal

        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response(
                {"error": "CSV file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account_id = request.data.get("account")
        if not account_id:
            return Response(
                {"error": "account is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account = self.account_service.get_account_by_id(int(account_id), request.user)
        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        ending_balance = None
        ending_date = None

        raw_balance = request.data.get("ending_balance")
        if raw_balance is not None and raw_balance != "":
            try:
                ending_balance = Decimal(str(raw_balance))
            except Exception:
                return Response(
                    {"error": "Invalid ending_balance"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        raw_date = request.data.get("ending_date")
        if raw_date:
            try:
                ending_date = date_type.fromisoformat(raw_date)
            except ValueError:
                return Response(
                    {"error": "Invalid ending_date format (use YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            result = self.statement_service.import_statement(
                account=account,
                statement_file=csv_file,
                institution="generic",
                statement_status="closed",
                ending_balance=ending_balance,
                ending_date=ending_date,
            )
        except Exception as e:
            logger.error(f"CSV import failed for account {account_id}: {str(e)}")
            return Response(
                {"error": f"Import failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        account.refresh_from_db(fields=["balance"])
        response_data = {
            "imported": result.imported_count,
            "skipped_duplicates": result.duplicate_count,
            "errors": result.errors,
            "balance_after_import": str(account.balance),
        }

        if ending_balance is not None:
            discrepancy = result.reconciliation.get("account_ending_discrepancy")
            if discrepancy is not None:
                response_data["discrepancy"] = discrepancy
            response_data["reconciliation_warnings"] = result.reconciliation_warnings

        return Response(response_data, status=status.HTTP_200_OK)


class StatementImportAPIView(APIView):
    """Preview or import CSV/Excel statements for supported institutions."""

    authentication_classes = [SessionAuthentication, TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()
        self.statement_service = StatementImportService()

    def get(self, request):
        """Return supported statement import institutions."""
        return Response(
            {"institutions": self.statement_service.get_supported_institutions()},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Preview or commit a CSV/XLS/XLSX statement import."""
        statement_file = request.FILES.get("file")
        if not statement_file:
            return Response({"error": "Statement file is required"}, status=status.HTTP_400_BAD_REQUEST)

        account_id = request.data.get("account")
        if not account_id:
            return Response({"error": "account is required"}, status=status.HTTP_400_BAD_REQUEST)

        institution = request.data.get("institution")
        if not institution:
            return Response({"error": "institution is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            raw_account_id = int(account_id)
        except (TypeError, ValueError):
            return Response({"error": "Invalid account"}, status=status.HTTP_400_BAD_REQUEST)

        account = self.account_service.get_account_by_id(raw_account_id, request.user)

        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        mode = request.data.get("mode", "preview")
        statement_period = request.data.get("statement_period", "")
        statement_status = request.data.get("statement_status", "provisional")
        if statement_status not in {"provisional", "closed"}:
            return Response(
                {"error": "statement_status must be provisional or closed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if mode == "commit":
                apply_opening_balance = self._bool_from_request(request, "apply_opening_balance")
                result = self.statement_service.import_statement(
                    account=account,
                    statement_file=statement_file,
                    institution=institution,
                    statement_period=statement_period,
                    statement_status=statement_status,
                    apply_opening_balance=apply_opening_balance,
                )
                # User-driven uploads of statement files bump a manual account
                # into the "upload" sync mode so the UI badge stays accurate.
                if account.sync_mode == "manual":
                    account.sync_mode = "upload"
                    account.save(update_fields=["sync_mode", "updated_at"])
            elif mode == "preview":
                result = self.statement_service.preview_statement(
                    account=account,
                    statement_file=statement_file,
                    institution=institution,
                    statement_period=statement_period,
                    statement_status=statement_status,
                )
            else:
                return Response(
                    {"error": "mode must be preview or commit"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            logger.error(f"Statement import failed for account {account_id}: {str(e)}")
            return Response(
                {"error": f"Import failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result.as_dict(), status=status.HTTP_200_OK)

    def _bool_from_request(self, request, key: str) -> bool:
        value = request.data.get(key)
        if isinstance(value, bool):
            return value
        if value in (None, ""):
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "on"}


class AgentStatementUploadAPIView(APIView):
    """Accept a bank-agent downloaded statement and store/import it through Richtato."""

    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statement_file_service = StatementFileService()

    def post(self, request):
        statement_file = request.FILES.get("file")
        if not statement_file:
            return Response({"error": "Statement file is required"}, status=status.HTTP_400_BAD_REQUEST)

        storage_uri = request.data.get("storage_uri", "")
        if not storage_uri:
            return Response({"error": "storage_uri is required"}, status=status.HTTP_400_BAD_REQUEST)

        from apps.financial_account.models import FinancialAccount

        account = (
            FinancialAccount.objects.select_related("institution", "user")
            .filter(
                user=request.user,
                storage_uri=storage_uri,
                is_active=True,
            )
            .first()
        )
        if not account:
            return Response({"error": "Account not found for storage_uri"}, status=status.HTTP_404_NOT_FOUND)

        institution = parser_key_for_account(account)
        if not institution:
            return Response({"error": "No statement parser configured for account"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            year = self._int_or_none(request.data.get("statement_year"))
            month = self._int_or_none(request.data.get("statement_month"))
            statement_period = request.data.get("statement_period") or (f"{year}-{month:02d}" if year and month else "")
            upload = self.statement_file_service.save_upload(
                user=request.user,
                account=account,
                uploaded_file=statement_file,
                institution=institution,
                statement_period=statement_period,
                statement_status="provisional",
                statement_year=year,
                statement_month=month,
                source="agent_drop",
            )
            result = None
            if upload.statement.import_status != "imported":
                result = self.statement_file_service.import_statement(upload.statement)
                upload.statement.refresh_from_db()
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Agent statement upload failed")
            return Response({"error": f"Upload failed: {exc}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {
                "statement": self.statement_file_service.serialize(upload.statement),
                "created": upload.created,
                "result": result.as_dict() if result else upload.statement.last_import_result,
            },
            status=status.HTTP_201_CREATED if upload.created else status.HTTP_200_OK,
        )

    def _int_or_none(self, value):
        if value in (None, ""):
            return None
        return int(value)


class AgentBalanceSnapshotAPIView(APIView):
    """Accept a bank-agent scraped balance snapshot for an investment account."""

    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()
        self.balance_service = AccountBalanceService()

    def post(self, request):
        from datetime import date as date_type
        from decimal import Decimal

        account_id = request.data.get("account_id")
        balance = request.data.get("balance")
        balance_date = request.data.get("date")

        if not all([account_id, balance is not None, balance_date]):
            return Response(
                {"error": "account_id, balance, and date are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account = self.account_service.get_account_by_id(int(account_id), request.user)
        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            balance_decimal = Decimal(str(balance))
        except Exception:
            return Response(
                {"error": "Invalid balance value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parsed_balance_date = date_type.fromisoformat(str(balance_date))
        except ValueError:
            return Response(
                {"error": "Invalid date format (use YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_balance = account.balance
        updated_account = self.balance_service.set_balance_snapshot(
            account=account,
            new_balance=balance_decimal,
            balance_date=parsed_balance_date,
            source="agent_sync",
        )

        return Response(
            {
                "balance": str(updated_account.balance),
                "date": str(parsed_balance_date),
                "previous_balance": str(old_balance),
                "adjustment": str(updated_account.balance - old_balance),
            },
            status=status.HTTP_200_OK,
        )


class StatementFileListCreateAPIView(APIView):
    """List statement library files or upload a new Google Drive statement file."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()
        self.statement_file_service = StatementFileService()

    def get(self, request):
        """List statement files and account/year/month folder tree."""
        filters = {
            "account_id": self._int_or_none(request.query_params.get("account")),
            "year": self._int_or_none(request.query_params.get("year")),
            "month": self._int_or_none(request.query_params.get("month")),
            "institution": request.query_params.get("institution") or None,
            "import_status": request.query_params.get("import_status") or None,
        }
        statements = list(self.statement_file_service.list_statements(request.user, **filters))
        return Response(
            {
                "rows": [self.statement_file_service.serialize(statement) for statement in statements],
                "tree": self.statement_file_service.build_folder_tree(
                    self.statement_file_service.list_statements(request.user)
                ),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Store an uploaded statement in the account's Google Drive folder."""
        statement_file = request.FILES.get("file")
        if not statement_file:
            return Response({"error": "Statement file is required"}, status=status.HTTP_400_BAD_REQUEST)

        account = self._get_account(request)
        if isinstance(account, Response):
            return account

        institution = request.data.get("institution") or parser_key_for_account(account)
        if not institution:
            return Response({"error": "No statement parser configured for account"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = self.statement_file_service.save_upload(
                user=request.user,
                account=account,
                uploaded_file=statement_file,
                institution=institution,
                statement_period=request.data.get("statement_period", ""),
                statement_status=request.data.get("statement_status", "provisional"),
                statement_year=self._int_or_none(request.data.get("statement_year")),
                statement_month=self._int_or_none(request.data.get("statement_month")),
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Statement upload failed: {str(e)}")
            return Response({"error": f"Upload failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {
                "statement": self.statement_file_service.serialize(result.statement),
                "created": result.created,
            },
            status=status.HTTP_201_CREATED if result.created else status.HTTP_200_OK,
        )

    def _get_account(self, request):
        from apps.financial_account.models import FinancialAccount

        account_id = request.data.get("account")
        if not account_id:
            return Response({"error": "account is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            account = self.account_service.get_account_by_id(int(account_id), request.user)
        except (TypeError, ValueError):
            return Response({"error": "Invalid account"}, status=status.HTTP_400_BAD_REQUEST)
        if not account:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        return FinancialAccount.objects.select_related("institution").get(pk=account.pk)

    def _int_or_none(self, value):
        if value in (None, ""):
            return None
        return int(value)


class StatementFileDetailAPIView(APIView):
    """Retrieve, update, or soft-delete a statement file."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()
        self.statement_file_service = StatementFileService()

    def get(self, request, pk: int):
        statement = self.statement_file_service.get_statement(request.user, pk)
        if not statement:
            return Response({"error": "Statement not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.statement_file_service.serialize(statement), status=status.HTTP_200_OK)

    def patch(self, request, pk: int):
        statement = self.statement_file_service.get_statement(request.user, pk)
        if not statement:
            return Response({"error": "Statement not found"}, status=status.HTTP_404_NOT_FOUND)

        account = None
        if "account" in request.data:
            try:
                account = self.account_service.get_account_by_id(int(request.data["account"]), request.user)
            except (TypeError, ValueError):
                return Response({"error": "Invalid account"}, status=status.HTTP_400_BAD_REQUEST)
            if not account:
                return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            if request.data.get("reconciliation_acknowledged") is True:
                updated = self.statement_file_service.acknowledge_reconciliation(statement)
                return Response(self.statement_file_service.serialize(updated), status=status.HTTP_200_OK)

            updated = self.statement_file_service.update_statement(
                statement,
                account=account,
                institution=request.data.get("institution"),
                statement_period=request.data.get("statement_period"),
                statement_status=request.data.get("statement_status"),
                statement_year=self._int_or_none(request.data.get("statement_year")),
                statement_month=self._int_or_none(request.data.get("statement_month")),
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.statement_file_service.serialize(updated), status=status.HTTP_200_OK)

    def delete(self, request, pk: int):
        statement = self.statement_file_service.get_statement(request.user, pk)
        if not statement:
            return Response({"error": "Statement not found"}, status=status.HTTP_404_NOT_FOUND)
        self.statement_file_service.soft_delete_statement(statement)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _int_or_none(self, value):
        if value in (None, ""):
            return None
        return int(value)


class StatementFileDownloadAPIView(APIView):
    """Download a stored Google Drive statement file."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statement_file_service = StatementFileService()

    def get(self, request, pk: int):
        statement = self.statement_file_service.get_statement(request.user, pk)
        if not statement:
            return Response({"error": "Statement not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            return self.statement_file_service.download_response(statement)
        except FileNotFoundError:
            return Response({"error": "Stored statement file not found"}, status=status.HTTP_404_NOT_FOUND)


class StatementFilePreviewAPIView(APIView):
    """Preview import from a stored Google Drive statement file."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statement_file_service = StatementFileService()

    def post(self, request, pk: int):
        statement = self.statement_file_service.get_statement(request.user, pk)
        if not statement:
            return Response({"error": "Statement not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            result = self.statement_file_service.preview_statement(statement)
        except Exception as e:
            logger.error(f"Statement preview failed for {pk}: {str(e)}")
            return Response({"error": f"Preview failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        statement.refresh_from_db()
        return Response(
            {
                "statement": self.statement_file_service.serialize(statement),
                "result": result.as_dict(),
            },
            status=status.HTTP_200_OK,
        )


class StatementFileImportAPIView(APIView):
    """Commit import from a stored Google Drive statement file."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statement_file_service = StatementFileService()

    def post(self, request, pk: int):
        statement = self.statement_file_service.get_statement(request.user, pk)
        if not statement:
            return Response({"error": "Statement not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            apply_opening_balance = self._bool_from_request(request, "apply_opening_balance")
            result = self.statement_file_service.import_statement(
                statement,
                apply_opening_balance=apply_opening_balance,
            )
        except Exception as e:
            logger.error(f"Statement import failed for {pk}: {str(e)}")
            return Response({"error": f"Import failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        statement.refresh_from_db()
        return Response(
            {
                "statement": self.statement_file_service.serialize(statement),
                "result": result.as_dict(),
            },
            status=status.HTTP_200_OK,
        )

    def _bool_from_request(self, request, key: str) -> bool:
        value = request.data.get(key)
        if isinstance(value, bool):
            return value
        if value in (None, ""):
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
