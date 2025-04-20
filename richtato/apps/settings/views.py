from datetime import datetime

from django.shortcuts import get_object_or_404, render
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from richtato.apps.account.models import Account
from richtato.apps.richtato_user.models import (
    CardAccount,
    Category,
    supported_card_banks,
)

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
    def get(self, request):
        cards = CardAccount.objects.filter(user=request.user).order_by("name")

        data = []
        for card in cards:
            data.append(
                {
                    "id": card.id,
                    "name": card.name,
                    "bank": card.card_bank_title,
                }
            )
        logger.debug(f"Get Cards: {data}")
        return Response(data)

    def post(self, request):
        serializer = CardAccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        logger.debug(f"Patch request data: {request.data}")
        card = get_object_or_404(CardAccount, pk=pk, user=request.user)
        serializer = CardAccountSerializer(card, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            logger.debug(f"Updated card account {pk}: {serializer.data}")
            return Response(serializer.data)
        else:
            logger.error(f"Error updating card account {pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        card = get_object_or_404(CardAccount, pk=pk, user=request.user)
        card.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CardAccountFieldChoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "bank": [
                {"value": value, "label": label}
                for value, label in supported_card_banks
            ],
        }
        return Response(data)
