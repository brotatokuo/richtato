"""Views for financial accounts API."""

from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
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
from apps.financial_account.services.csv_import_service import CSVImportService


class FinancialAccountListCreateAPIView(APIView):
    """List all accounts or create a new manual account."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()

    def get(self, request):
        """List all financial accounts for the user."""
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        account_type = request.query_params.get("type")

        if account_type:
            accounts = self.account_service.get_accounts_by_type(request.user, account_type)
        else:
            accounts = self.account_service.get_user_accounts(request.user, active_only=active_only)

        serializer = FinancialAccountSerializer(accounts, many=True)
        # Return both formats for compatibility
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

        serializer = FinancialAccountUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated_account = self.account_service.update_account(account, **serializer.validated_data)
            response_serializer = FinancialAccountSerializer(updated_account)
            return Response(response_serializer.data)

        except Exception as e:
            logger.error(f"Error updating account {pk}: {str(e)}")
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
        from apps.financial_account.models import FinancialAccount, FinancialInstitution

        # Account type choices
        type_choices = [{"value": choice[0], "label": choice[1]} for choice in FinancialAccount.ACCOUNT_TYPE_CHOICES]

        # Entity/institution choices - use slug as value for consistency with frontend
        # Sort alphabetically but keep "Other" at the end
        institutions = FinancialInstitution.objects.all().order_by("name")
        entity_choices = []
        other_choice = None

        for inst in institutions:
            choice = {"value": inst.slug, "label": inst.name}
            if inst.slug == "other":
                other_choice = choice
            else:
                entity_choices.append(choice)

        # Add "Other" at the end if it exists
        if other_choice:
            entity_choices.append(other_choice)

        return Response({"type": type_choices, "entity": entity_choices})


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
    """Import transactions from a CSV statement file."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_service = AccountService()
        self.csv_service = CSVImportService()

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
            result = self.csv_service.import_statement(
                account=account,
                csv_file=csv_file,
                ending_balance=ending_balance,
                ending_date=ending_date,
            )
        except Exception as e:
            logger.error(f"CSV import failed for account {account_id}: {str(e)}")
            return Response(
                {"error": f"Import failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = {
            "imported": result.imported_count,
            "skipped_duplicates": result.skipped_duplicates,
            "errors": result.errors,
            "balance_after_import": (
                str(result.balance_after_import) if result.balance_after_import is not None else None
            ),
        }

        if result.discrepancy is not None:
            response_data["discrepancy"] = str(result.discrepancy)
            response_data["adjustment"] = str(result.adjustment_amount)

        return Response(response_data, status=status.HTTP_200_OK)
