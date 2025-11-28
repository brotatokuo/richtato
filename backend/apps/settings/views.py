from datetime import datetime

from django.shortcuts import get_object_or_404, render
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.account.models import Account
from apps.richtato_user.models import (
    CardAccount,
    Category,
    supported_card_banks,
)
from apps.richtato_user.services.card_account_service import CardAccountService

from .serializers import CardAccountSerializer


def main(request):
    category_list = list(Category.objects.filter(user=request.user))
    return render(
        request,
        "old_settings.html",
        {
            "account_types": Account.account_types,
            "category_list": category_list,
            "today_date": datetime.today().strftime("%Y-%m-%d"),
            "category_types": Category.CATEGORY_TYPES,
        },
    )


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class CardAccountAPIView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.card_account_service = CardAccountService()

    def get(self, request):
        cards = CardAccount.objects.filter(user=request.user).order_by("name")

        rows = []
        for card in cards:
            rows.append(
                {
                    "id": card.id,
                    "name": card.name,
                    "bank": card.card_bank_title,
                }
            )
        data = {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "name", "title": "Name"},
                {"field": "bank", "title": "Bank"},
            ],
            "rows": rows,
        }

        return Response(data)

    def post(self, request):
        data = request.data.copy()
        logger.debug(f"Post request data: {data}")
        data["account_name"] = data.get("Name", None)
        serializer = CardAccountSerializer(data=data)
        if serializer.is_valid():
            name = serializer.validated_data["name"]
            bank = serializer.validated_data["bank"]
            card_data = self.card_account_service.create_card_account(
                request.user, name, bank
            )
            return Response(card_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        logger.debug(f"Patch request data: {request.data}")
        serializer = CardAccountSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            try:
                card_data = self.card_account_service.update_card_account(
                    pk, request.user, **serializer.validated_data
                )
                logger.debug(f"Updated card account {pk}: {card_data}")
                return Response(card_data)
            except ValueError as e:
                logger.error(f"Error updating card account {pk}: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        else:
            logger.error(f"Error updating card account {pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            self.card_account_service.delete_card_account(pk, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class CardAccountFieldChoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.card_account_service = CardAccountService()

    def get(self, request):
        data = self.card_account_service.get_field_choices()
        return Response(data)
