import pytz
from django.db.models import F
from django.shortcuts import (
    get_object_or_404,
)
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from richtato.apps.settings.models import CardAccount, Category
from richtato.views import BaseAPIView

from .models import Expense
from .serializers import ExpenseSerializer

pst = pytz.timezone("US/Pacific")


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class ExpenseAPIView(BaseAPIView):
    @property
    def field_remap(self):
        return {
            "Account": "account_name__name",
            "Category": "category__name",
        }

    def get(self, request):
        """
        Get the most recent entries for the user.
        """
        limit_param = request.GET.get("limit", None)

        try:
            limit = int(limit_param) if limit_param is not None else None
        except ValueError:
            return Response({"error": "Invalid limit value"}, status=400)

        entries = (
            Expense.objects.filter(user=request.user)
            .annotate(
                Account=F("account_name__name"),
                Category=F("category__name"),
            )
            .order_by("-date")
            .values(
                "id",
                "date",
                "description",
                "amount",
                "Account",
                "Category",
            )
        )

        if limit is not None:
            logger.debug(f"Limit: {limit}")
            entries = entries[:limit]

        return Response(entries)

    def post(self, request):
        """
        Create a new expense entry.
        """
        logger.debug(f"Request data: {request.data}")
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """
        Update an existing expense entry.
        """
        logger.debug(f"PATCH request data: {request.data}")
        reversed_data = self.apply_fieldmap(request.data)
        logger.debug(f"Reversed data: {reversed_data}")
        expense = get_object_or_404(Expense, pk=pk, user=request.user)

        serializer = ExpenseSerializer(expense, data=reversed_data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        else:
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete an existing expense entry.
        """
        logger.debug(f"DELETE request for expense with pk: {pk}")
        expense = get_object_or_404(Expense, pk=pk, user=request.user)

        expense.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExpenseFieldChoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_card_accounts = CardAccount.objects.filter(user=request.user)
        user_categories = Category.objects.filter(user=request.user)
        data = {
            "account": [
                {"value": account.id, "label": account.name}
                for account in user_card_accounts
            ],
            "ategory": [
                {"value": category.id, "label": category.name}
                for category in user_categories
            ],
        }
        return Response(data)
