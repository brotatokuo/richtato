"""Views for financial accounts API."""

from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.financial_account.serializers import (
    AccountBalanceHistorySerializer,
    FinancialAccountCreateSerializer,
    FinancialAccountSerializer,
    FinancialAccountUpdateSerializer,
)
from apps.financial_account.services.account_balance_service import (
    AccountBalanceService,
)
from apps.financial_account.services.account_service import AccountService
from loguru import logger


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
            accounts = self.account_service.get_accounts_by_type(
                request.user, account_type
            )
        else:
            accounts = self.account_service.get_user_accounts(
                request.user, active_only=active_only
            )

        serializer = FinancialAccountSerializer(accounts, many=True)
        return Response({"accounts": serializer.data})

    def post(self, request):
        """Create a new manual financial account."""
        serializer = FinancialAccountCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = self.account_service.create_manual_account(
                user=request.user, **serializer.validated_data
            )

            response_serializer = FinancialAccountSerializer(account)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating manual account: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = FinancialAccountSerializer(account)
        return Response(serializer.data)

    def patch(self, request, pk):
        """Update account."""
        account = self.account_service.get_account_by_id(pk, request.user)

        if not account:
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = FinancialAccountUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated_account = self.account_service.update_account(
                account, **serializer.validated_data
            )
            response_serializer = FinancialAccountSerializer(updated_account)
            return Response(response_serializer.data)

        except Exception as e:
            logger.error(f"Error updating account {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """Delete (deactivate) account."""
        account = self.account_service.get_account_by_id(pk, request.user)

        if not account:
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            self.account_service.delete_account(account)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error deleting account {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )

        days = int(request.query_params.get("days", 30))

        try:
            trend_data = self.balance_service.get_balance_trend(account, days=days)
            return Response(trend_data)

        except Exception as e:
            logger.error(f"Error getting balance history for account {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
