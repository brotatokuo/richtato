# views.py
from django.shortcuts import get_object_or_404
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from richtato.utilities.tools import format_currency, format_date

from .models import Account
from .serializers import AccountSerializer


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class AccountAPIView(APIView):
    def get(self, request):
        accounts = Account.objects.filter(user=request.user).order_by("name")

        data = []
        for account in accounts:
            data.append(
                {
                    "id": account.id,
                    "name": account.name,
                    "type": account.type.title(),
                    "entity": account.asset_entity_name.title(),
                    "balance": format_currency(account.latest_balance),
                    "date": format_date(account.latest_balance_date)
                    if account.latest_balance_date
                    else None,
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
        account = get_object_or_404(Account, pk=pk, user=request.user)

        serializer = AccountSerializer(account, data=request.data, partial=True)
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
