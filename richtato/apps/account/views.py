from django.db.models import F
from django.shortcuts import get_object_or_404
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from richtato.utilities.tools import format_currency, format_date
from richtato.views import BaseAPIView

from .models import Account, AccountTransaction, account_types, supported_asset_accounts
from .serializers import AccountSerializer, AccountTransactionSerializer


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class AccountAPIView(BaseAPIView):
    @property
    def field_remap(self):
        return {
            "entity": "asset_entity_name",
            "balance": "latest_balance",
            "date": "latest_balance_date",
        }

    def get(self, request):
        annotate_fields = {key: F(value) for key, value in self.field_remap.items()}

        accounts = (
            Account.objects.filter(user=request.user)
            .annotate(**annotate_fields)
            .order_by("name")
            .values("id", "name", "type", "entity", "balance", "date")
        )

        rows = []
        for account in accounts:
            rows.append(
                {
                    **account,
                    "type": account["type"].title(),
                    "entity": account["entity"].title(),
                    "balance": format_currency(account["balance"]),
                    "date": format_date(account["date"]) if account["date"] else None,
                }
            )
        data = {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "name", "title": "Name"},
                {"field": "type", "title": "Type"},
                {"field": "entity", "title": "Entity"},
                {"field": "balance", "title": "Balance"},
            ],
            "rows": rows,
        }
        return Response(data)

    def post(self, request):
        logger.debug(f"Request data: {request.data}")
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
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
        logger.debug(f"DELETE request for account with pk: {pk}")
        account = get_object_or_404(Account, pk=pk, user=request.user)

        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountFieldChoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "type": [
                {"value": value, "label": label} for value, label in account_types
            ],
            "entity": [
                {"value": value, "label": label}
                for value, label in supported_asset_accounts
            ],
        }
        return Response(data)


class AccountTransactionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        account = get_object_or_404(Account, pk=pk, user=request.user)
        transactions = AccountTransaction.objects.filter(account=account).order_by(
            "-date"
        )
        data = {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "amount", "title": "Amount"},
                {"field": "description", "title": "Description"},
            ],
            "rows": [
                {
                    "id": transaction.id,
                    "date": format_date(transaction.date),
                    "amount": format_currency(transaction.amount),
                }
                for transaction in transactions
            ],
        }
        return Response(data)


class AccountDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        user = request.user
        limit_param = request.GET.get("limit", None)

        try:
            limit = int(limit_param) if limit_param is not None else None
        except ValueError:
            return Response({"error": "Invalid limit value"}, status=400)

        if pk:
            account = get_object_or_404(Account, pk=pk, user=user)
            transactions = AccountTransaction.objects.filter(account=account).order_by(
                "-date"
            )
        else:
            transactions = AccountTransaction.objects.filter(
                account__user=user
            ).order_by("-date")

        if limit is not None:
            transactions = transactions[:limit]

        data = {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "amount", "title": "Amount"},
                {"field": "account", "title": "Account"},
            ],
            "rows": [
                {
                    "id": t.id,
                    "date": format_date(t.date),
                    "amount": format_currency(t.amount),
                    "account": t.account.name,
                }
                for t in transactions
            ],
        }

        return Response(data)

    def post(self, request):
        logger.debug(f"POST request data: {request.data}")
        serializer = AccountTransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountDetailFieldChoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_accounts_dict = self._get_user_accounts(request.user)
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

    def _get_user_accounts(self, user) -> list[dict]:
        user_accounts = Account.objects.filter(user=user).values("id", "name")
        return [{"value": acc["id"], "label": acc["name"]} for acc in user_accounts]
