"""
Account views - Thin HTTP wrappers delegating to service layer.

Following clean architecture: Views handle only HTTP concerns.
Business logic is in services, database access is in repositories.
"""

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from richtato.views import BaseAPIView

from .models import Account
from .repositories import AccountRepository, AccountTransactionRepository
from .serializers import AccountSerializer, AccountTransactionSerializer
from .services import AccountService, AccountTransactionService


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class AccountAPIView(BaseAPIView):
    """ViewSet for managing accounts - THIN WRAPPER."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.account_repo = AccountRepository()
        self.transaction_repo = AccountTransactionRepository()
        # Inject services with dependencies
        self.account_service = AccountService(self.account_repo, self.transaction_repo)

    @property
    def field_remap(self):
        return {
            "entity": "asset_entity_name",
            "balance": "latest_balance",
            "date": "latest_balance_date",
        }

    def get(self, request):
        """Get all accounts for user - delegates to service layer."""
        data = self.account_service.get_user_accounts_formatted(request.user)
        return Response(data)

    def post(self, request):
        """Create a new account - delegates to service layer."""
        logger.debug(f"Request data: {request.data}")
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Update an existing account - delegates to service layer."""
        logger.debug(f"PATCH request data: {request.data}")
        reversed_data = self.apply_fieldmap(request.data)
        account = get_object_or_404(Account, pk=pk, user=request.user)

        serializer = AccountSerializer(account, data=reversed_data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        else:
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete an existing account - delegates to service layer."""
        logger.debug(f"DELETE request for account with pk: {pk}")
        account = get_object_or_404(Account, pk=pk, user=request.user)

        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountFieldChoicesAPIView(APIView):
    """Get field choices for account creation - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get field choices - delegates to service layer."""
        data = AccountService.get_field_choices()
        return Response(data)


class AccountTransactionsAPIView(APIView):
    """Manage account transactions - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.account_repo = AccountRepository()
        self.transaction_repo = AccountTransactionRepository()
        # Inject service with dependencies
        self.transaction_service = AccountTransactionService(
            self.account_repo, self.transaction_repo
        )

    def get(self, request, pk):
        """Get paginated transactions for account - delegates to service layer."""
        account = get_object_or_404(Account, pk=pk, user=request.user)

        # Extract pagination parameters
        try:
            page = max(1, int(request.GET.get("page", "1")))
            page_size = max(1, min(100, int(request.GET.get("page_size", "10"))))
        except ValueError:
            page = 1
            page_size = 10

        # Delegate to service
        data = self.transaction_service.get_paginated_transactions(
            account, page, page_size
        )
        return Response(data)

    def patch(self, request, pk):
        """Update a transaction - delegates to service layer."""
        account = get_object_or_404(Account, pk=pk, user=request.user)
        transaction_id = request.data.get("id")

        if not transaction_id:
            return Response({"error": "Missing transaction id"}, status=400)

        # Delegate to service
        updated_transaction, error = self.transaction_service.update_transaction(
            account, transaction_id, request.data
        )

        if error:
            return Response(
                {"error": error}, status=404 if "not found" in error else 400
            )

        # Format response
        from utilities.tools import format_currency, format_date

        return Response(
            {
                "id": updated_transaction.id,
                "date": format_date(updated_transaction.date),
                "amount": format_currency(updated_transaction.amount),
            }
        )

    def delete(self, request, pk):
        """Delete a transaction and recalculate balance - delegates to service layer."""
        account = get_object_or_404(Account, pk=pk, user=request.user)
        transaction_id = request.data.get("id") or request.GET.get("id")

        if not transaction_id:
            return Response({"error": "Missing transaction id"}, status=400)

        # Delegate to service
        (
            success,
            error,
        ) = self.transaction_service.delete_transaction_and_recompute_balance(
            account, int(transaction_id)
        )

        if error:
            return Response({"error": error}, status=404)

        return Response(status=204)


class AccountDetailAPIView(APIView):
    """Get account transaction details - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.account_repo = AccountRepository()
        self.transaction_repo = AccountTransactionRepository()
        # Inject service with dependencies
        self.transaction_service = AccountTransactionService(
            self.account_repo, self.transaction_repo
        )

    def get(self, request, pk=None):
        """Get account transactions - delegates to service layer."""
        user = request.user

        # Extract limit parameter
        try:
            limit = int(request.GET.get("limit")) if request.GET.get("limit") else None
        except ValueError:
            return Response({"error": "Invalid limit value"}, status=400)

        # Delegate to service
        data = self.transaction_service.get_user_transactions_formatted(user, limit)
        return Response(data)

    def post(self, request):
        """Create a new transaction - delegates to service layer."""
        logger.debug(f"POST request data: {request.data}")
        serializer = AccountTransactionSerializer(data=request.data)
        if serializer.is_valid():
            # Get account and use service to create transaction
            account_id = request.data.get("account")
            account = get_object_or_404(Account, pk=account_id, user=request.user)

            # Delegate to service
            transaction, error = self.transaction_service.create_transaction(
                account,
                serializer.validated_data["amount"],
                serializer.validated_data["date"],
            )

            if error:
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

            response_serializer = AccountTransactionSerializer(transaction)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountDetailFieldChoicesAPIView(APIView):
    """Get field choices for account details - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.account_repo = AccountRepository()

    def get(self, request):
        """Get field choices - delegates to repository layer."""
        user_accounts_list = self.account_repo.get_user_accounts_for_choices(
            request.user
        )
        user_accounts_dict = [
            {"value": acc["id"], "label": acc["name"]} for acc in user_accounts_list
        ]

        data = {
            "type": [
                {"value": "checking", "label": "Checking"},
                {"value": "savings", "label": "Savings"},
            ],
            "asset_entity_name": [
                {"value": "bank", "label": "Bank"},
                {"value": "investment", "label": "Investment"},
            ],
            "account": user_accounts_dict,
        }
        return Response(data)


class AccountTransactionChartView(TemplateView):
    """Template view for account transaction chart."""

    template_name = "account_transaction_chart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account_id = kwargs["account_id"]

        account = get_object_or_404(Account, pk=account_id, user=self.request.user)
        context["account"] = account
        context["account_id"] = account_id

        return context
