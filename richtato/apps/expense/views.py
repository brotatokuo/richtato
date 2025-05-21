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

from richtato.apps.expense.imports import ExpenseManager
from richtato.apps.richtato_user.utils import (
    _get_line_graph_data_by_day,
    _get_line_graph_data_by_month,
)
from richtato.apps.settings.models import CardAccount, Category
from richtato.google_gemini.ai import AI
from richtato.statement_imports.cards.card_factory import CardStatement
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
        
        data = {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "description", "title": "Description"},
                {"field": "amount", "title": "Amount"},
                {"field": "Account", "title": "Account"},
                {"field": "Category", "title": "Category"},
            ],
            "rows": entries,
        }
        return Response(data)

    def post(self, request):
        """
        Create a new expense entry.
        """
        logger.debug(f"Request data: {request.data}")
        #HACK
        modified_data = request.data.copy()
        modified_data["account_name"] = modified_data.pop("Account", None)
        modified_data["category"] = modified_data.pop("Category", None)
        modified_data["user"] = request.user.id
        logger.debug(f"Modified data: {modified_data}")
        
        serializer = ExpenseSerializer(data=modified_data)
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


class ExpenseGraphAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_range = request.query_params.get("range", "all")
        logger.debug(f"Date range: {date_range}")

        if date_range == "all":
            chart_data = _get_line_graph_data_by_month(request.user, Expense)
        elif date_range == "30d":
            logger.debug("Getting data for the last 30 days")
            chart_data = _get_line_graph_data_by_day(request.user, Expense)
        else:
            return Response({"error": "Invalid range. Use '30d' or 'all'."}, status=400)

        return Response(
            {
                "labels": chart_data["labels"],
                "datasets": [
                    {
                        "label": "Expense",
                        "data": chart_data["values"],
                        "backgroundColor": "rgba(232, 82, 63, 0.2)",
                        "borderColor": "rgba(232, 82, 63, 1)",
                        "borderWidth": 1,
                    }
                ],
            }
        )


class ExpenseFieldChoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_card_accounts = CardAccount.objects.filter(user=request.user)
        user_categories = Category.objects.filter()
        data = {
            "account": [
                {"value": account.id, "label": account.name}
                for account in user_card_accounts
            ],
            "category": [
                {"value": category.id, "label": category.name}
                for category in user_categories
            ],
        }
        return Response(data)


class CategorizeTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Categorize a transaction based on the description.
        """
        description = request.data.get("description")
        if not description:
            return Response({"error": "Description is required."}, status=400)

        # Use AI to categorize the transaction
        category = AI.categorize_transaction(request.user, description)

        cateogry_id = (
            Category.objects.filter(name=category).first().id
        )
        logger.debug(f"Categorized as: {category}")
        return Response({"category": cateogry_id})


class ImportStatementsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Import statements and categorize transactions.
        """

        # Assuming the request contains a file with transactions
        def ensure_list(obj):
            if obj is None:
                return []
            if isinstance(obj, list):
                return obj
            return [obj]

        # Usage
        files = ensure_list(request.FILES.getlist("files"))  # For files specifically
        card_accounts = ensure_list(request.data.get("card_accounts"))

        # Process the files and categorize transactions
        for file, card_account in zip(files, card_accounts):
            card = CardAccount.objects.get(id=card_account, user=request.user)
            logger.debug(f"Card: {card}")
            card_statement = CardStatement.create_from_file(
                request.user,
                card.bank,
                card.name,
                file,
            )
            logger.debug(card_statement.formatted_df)
            ExpenseManager.import_from_dataframe(
                card_statement.formatted_df, request.user
            )

        return Response({"message": "File processed successfully."})
