"""Service layer for graph and timeseries data generation."""

from datetime import datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta
from django.db.models import Sum

from apps.transaction.models import Transaction


class GraphService:
    """Service for generating graph and timeseries data using unified Transaction model."""

    def __init__(self):
        self.pst = pytz.timezone("US/Pacific")

    def get_combined_graph_data(self, user) -> dict:
        """Get combined income and expense graph data."""
        expense_data = self.get_transaction_data_by_month(user, "debit")
        income_data = self.get_transaction_data_by_month(user, "credit")

        chart_data = {
            "labels": expense_data["labels"],  # assumes income labels match
            "datasets": [
                {
                    "label": "Expenses",
                    "data": expense_data["values"],
                    "backgroundColor": "rgba(232, 82, 63, 0.2)",
                    "borderColor": "rgba(232, 82, 63, 0.5)",
                    "borderWidth": 1,
                    "fill": True,
                    "tension": 0.4,
                },
                {
                    "label": "Income",
                    "data": income_data["values"],
                    "backgroundColor": "rgba(152, 204, 44, 0.2)",
                    "borderColor": "rgba(152, 204, 44, 0.5)",
                    "borderWidth": 1,
                    "fill": True,
                    "tension": 0.4,
                },
            ],
        }

        return chart_data

    def get_transaction_data_by_month(
        self, user, transaction_type: str = "debit"
    ) -> dict:
        """Generate line graph data aggregated by month for a transaction type."""
        today = datetime.now(self.pst).date()

        # Get earliest transaction of this type
        earliest_transaction = (
            Transaction.objects.filter(user=user, transaction_type=transaction_type)
            .order_by("date")
            .first()
        )

        if earliest_transaction:
            start_date = earliest_transaction.date.replace(day=1)
        else:
            start_date = today.replace(day=1)

        # Generate months range from start date to today
        months_range = []
        current_month = start_date

        while current_month <= today:
            months_range.append(current_month.strftime("%b %Y"))
            current_month += relativedelta(months=1)

        # Query transactions
        transactions = Transaction.objects.filter(
            user=user,
            transaction_type=transaction_type,
            date__gte=start_date,
        ).order_by("date")

        line_graph_data = {month: 0 for month in months_range}

        for txn in transactions:
            month_year = txn.date.strftime("%b %Y")
            if month_year in line_graph_data:
                line_graph_data[month_year] += float(txn.amount)

        sorted_labels = list(months_range)
        sorted_data = [line_graph_data[label] for label in sorted_labels]

        chart_data = {
            "labels": sorted_labels,
            "values": sorted_data,
        }

        return chart_data

    def get_transaction_data_by_day(
        self, user, transaction_type: str = "debit"
    ) -> dict:
        """Generate line graph data aggregated by day (last 30 days)."""
        today = datetime.now(self.pst).date()
        start_date = today - timedelta(days=29)

        # Generate daily range
        days_range = [(start_date + timedelta(days=i)) for i in range(30)]
        formatted_days = [day.strftime("%b %d") for day in days_range]

        # Query transactions within the last 30 days
        transactions = Transaction.objects.filter(
            user=user,
            transaction_type=transaction_type,
            date__range=(start_date, today),
        ).order_by("date")

        line_graph_data = {day.strftime("%b %d"): 0 for day in days_range}

        for txn in transactions:
            day_label = txn.date.strftime("%b %d")
            if day_label in line_graph_data:
                line_graph_data[day_label] += float(txn.amount)

        chart_data = {
            "labels": formatted_days,
            "values": [line_graph_data[day] for day in formatted_days],
        }

        return chart_data
