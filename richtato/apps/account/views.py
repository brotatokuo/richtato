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

from .models import Account, account_types, supported_asset_accounts
from .serializers import AccountSerializer


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

        data = []
        for account in accounts:
            data.append(
                {
                    **account,
                    "type": account["type"].title(),
                    "entity": account["entity"].title(),
                    "balance": format_currency(account["balance"]),
                    "date": format_date(account["date"]) if account["date"] else None,
                }
            )

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
