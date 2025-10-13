import pytz
from apps.account.models import Account
from apps.richtato_user.utils import (
    _get_line_graph_data_by_day,
    _get_line_graph_data_by_month,
)
from django.db.models import F
from django.shortcuts import get_object_or_404
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from richtato.views import BaseAPIView

from .models import Income
from .serializers import IncomeSerializer

pst = pytz.timezone("US/Pacific")


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class IncomeAPIView(BaseAPIView):
    @property
    def field_remap(self):
        return {}

    def get(self, request):
        """
        Get the most recent entries for the user.
        """
        from datetime import datetime as _dt

        limit_param = request.GET.get("limit", None)
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        try:
            limit = int(limit_param) if limit_param is not None else None
        except ValueError:
            return Response({"error": "Invalid limit value"}, status=400)

        # Build base queryset
        qs = Income.objects.filter(user=request.user)

        # Optional date filtering
        try:
            if start_date_str:
                start_date = _dt.strptime(start_date_str, "%Y-%m-%d").date()
                qs = qs.filter(date__gte=start_date)
            if end_date_str:
                end_date = _dt.strptime(end_date_str, "%Y-%m-%d").date()
                qs = qs.filter(date__lte=end_date)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."}, status=400
            )

        entries = (
            qs.annotate(
                Account=F("account_name__name"),
            )
            .order_by("-date")
            .values(
                "id",
                "date",
                "Account",
                "description",
                "amount",
            )
        )

        if limit is not None:
            logger.debug(f"Limit: {limit}")
            entries = entries[:limit]

        data = {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "Account", "title": "Account"},
                {"field": "description", "title": "Description"},
                {"field": "amount", "title": "Amount"},
            ],
            "rows": entries,
        }

        return Response(data)

    def post(self, request):
        """
        Create a new Income entry.
        """
        logger.debug(f"Request data: {request.data}")
        serializer = IncomeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """
        Update an existing Income entry.
        """
        logger.debug(f"PATCH request data: {request.data}")
        reversed_data = self.apply_fieldmap(request.data)
        logger.debug(f"Reversed data: {reversed_data}")
        income = get_object_or_404(Income, pk=pk, user=request.user)

        serializer = IncomeSerializer(income, data=reversed_data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        else:
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete an existing Income entry.
        """
        logger.debug(f"DELETE request for Income with pk: {pk}")
        income = get_object_or_404(Income, pk=pk, user=request.user)

        income.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IncomeGraphAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_range = request.query_params.get("range", "all")
        logger.debug(f"Date range: {date_range}")
        if date_range == "all":
            chart_data = _get_line_graph_data_by_month(request.user, Income)
        elif date_range == "30d":
            logger.debug("Getting data for the last 30 days")
            chart_data = _get_line_graph_data_by_day(request.user, Income)
        else:
            return Response({"error": "Invalid range. Use '30d' or 'all'."}, status=400)
        return Response(
            {
                "labels": chart_data["labels"],
                "datasets": [
                    {
                        "label": "Income",
                        "data": chart_data["values"],
                        "backgroundColor": "rgba(152, 204, 44, 0.2)",
                        "borderColor": "rgba(152, 204, 44, 1)",
                        "borderWidth": 1,
                    }
                ],
            }
        )


class IncomeFieldChoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_accounts = Account.objects.filter(user=request.user)
        data = {
            "account": [
                {"value": account.id, "label": account.name}
                for account in user_accounts
            ],
        }
        return Response(data)
