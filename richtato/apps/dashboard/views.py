from datetime import timedelta

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from utilities.postgres.pg_client import PostgresClient

from richtato.apps.budget.models import Budget
from richtato.apps.expense.models import Expense
from richtato.apps.income.models import Income


@login_required
def cash_flow_data(request):
    """
    Get cash flow data with period filtering (income, expenses, net cash flow)
    """
    try:
        # Get period parameter from request
        period = request.GET.get("period", "6m")

        # Calculate date range based on period
        end_date = timezone.now().date()

        if period == "6m":
            start_date = end_date - relativedelta(months=6)
        elif period == "1y":
            start_date = end_date - relativedelta(years=1)
        elif period == "all":
            # For all time, get data from the earliest transaction
            earliest_income = (
                Income.objects.filter(user=request.user).order_by("date").first()
            )
            earliest_expense = (
                Expense.objects.filter(user=request.user).order_by("date").first()
            )

            if earliest_income and earliest_expense:
                start_date = min(earliest_income.date, earliest_expense.date)
            elif earliest_income:
                start_date = earliest_income.date
            elif earliest_expense:
                start_date = earliest_expense.date
            else:
                start_date = end_date - relativedelta(months=6)  # Default fallback
        else:
            # Default to 6 months
            start_date = end_date - relativedelta(months=6)

        # Generate monthly labels
        labels = []
        current_date = start_date.replace(day=1)
        while current_date <= end_date:
            labels.append(current_date.strftime("%b"))
            current_date += relativedelta(months=1)

        # Get income data by month
        income_data = []
        expense_data = []
        net_cash_flow = []

        for i, label in enumerate(labels):
            month_start = start_date.replace(day=1) + relativedelta(months=i)
            month_end = month_start + relativedelta(months=1) - timedelta(days=1)

            # Calculate income for this month
            monthly_income = (
                Income.objects.filter(
                    user=request.user, date__gte=month_start, date__lte=month_end
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            # Calculate expenses for this month
            monthly_expense = (
                Expense.objects.filter(
                    user=request.user, date__gte=month_start, date__lte=month_end
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            ) * -1

            income_data.append(float(monthly_income))
            expense_data.append(float(monthly_expense))
            net_cash_flow.append(float(monthly_income - monthly_expense))

        return JsonResponse(
            {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Net Cash Flow",
                        "data": net_cash_flow,
                        "borderColor": "#98CC2C",
                        "backgroundColor": "rgba(152, 204, 44, 0.1)",
                        "fill": True,
                        "tension": 0.4,
                    },
                    {
                        "label": "Income",
                        "data": income_data,
                        "borderColor": "#4CAF50",
                        "backgroundColor": "transparent",
                        "borderDash": [5, 5],
                    },
                    {
                        "label": "Expenses",
                        "data": expense_data,
                        "borderColor": "#FF6B6B",
                        "backgroundColor": "transparent",
                        "borderDash": [5, 5],
                    },
                ],
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def expense_categories_data(request):
    """
    Get expense breakdown by category for pie chart
    """
    try:
        # Get year and month from query params
        import calendar
        from datetime import date

        year = request.GET.get("year")
        month = request.GET.get("month")
        today = timezone.now().date()
        if year and month:
            year = int(year)
            month = int(month)
            start_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = date(year, month, last_day)
        else:
            # Default to current month
            start_date = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)

        expenses = (
            Expense.objects.filter(
                user=request.user, date__gte=start_date, date__lte=end_date
            )
            .values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")[:6]
        )  # Top 6 categories

        labels = [exp["category__name"] or "Uncategorized" for exp in expenses]
        data = [float(exp["total"]) for exp in expenses]

        # Color palette matching dashboard theme
        colors = ["#98CC2C", "#4CAF50", "#81C784", "#A5D6A7", "#C8E6C9", "#E8F5E8"]

        return JsonResponse(
            {
                "labels": labels,
                "datasets": [
                    {
                        "data": data,
                        "backgroundColor": colors[: len(data)],
                        "borderWidth": 2,
                        "borderColor": "#fff",
                    }
                ],
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def income_expenses_data(request):
    """
    Get monthly income vs expenses comparison
    """
    try:
        # Get data for last 6 months
        end_date = timezone.now().date()
        start_date = end_date - relativedelta(months=6)

        labels = []
        income_data = []
        expense_data = []

        current_date = start_date.replace(day=1)
        while current_date <= end_date:
            labels.append(current_date.strftime("%b"))

            month_end = current_date + relativedelta(months=1) - timedelta(days=1)

            monthly_income = (
                Income.objects.filter(
                    user=request.user, date__gte=current_date, date__lte=month_end
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            monthly_expense = (
                Expense.objects.filter(
                    user=request.user, date__gte=current_date, date__lte=month_end
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            ) * -1

            income_data.append(float(monthly_income))
            expense_data.append(float(monthly_expense))

            current_date += relativedelta(months=1)

        return JsonResponse(
            {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Income",
                        "data": income_data,
                        "backgroundColor": "#98CC2C",
                        "borderRadius": 4,
                    },
                    {
                        "label": "Expenses",
                        "data": expense_data,
                        "backgroundColor": "#FF6B6B",
                        "borderRadius": 4,
                    },
                ],
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def savings_data(request):
    """
    Get savings accumulation data
    """
    try:
        # Get data for last 6 months
        end_date = timezone.now().date()
        start_date = end_date - relativedelta(months=6)

        labels = []
        total_savings = []
        monthly_savings = []
        running_total = 0

        current_date = start_date.replace(day=1)
        while current_date <= end_date:
            labels.append(current_date.strftime("%b"))

            month_end = current_date + relativedelta(months=1) - timedelta(days=1)

            monthly_income = (
                Income.objects.filter(
                    user=request.user, date__gte=current_date, date__lte=month_end
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            monthly_expense = (
                Expense.objects.filter(
                    user=request.user, date__gte=current_date, date__lte=month_end
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            monthly_saving = float(monthly_income - monthly_expense)
            running_total += monthly_saving

            monthly_savings.append(monthly_saving)
            total_savings.append(running_total)

            current_date += relativedelta(months=1)

        return JsonResponse(
            {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Total Savings",
                        "data": total_savings,
                        "borderColor": "#98CC2C",
                        "backgroundColor": "rgba(152, 204, 44, 0.1)",
                        "fill": True,
                        "tension": 0.4,
                    },
                    {
                        "label": "Monthly Savings",
                        "data": monthly_savings,
                        "type": "bar",
                        "backgroundColor": "#4CAF50",
                        "borderRadius": 4,
                    },
                ],
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def budget_progress_data(request):
    """
    Get budget progress for current month
    """
    try:
        # Get current month data
        now = timezone.now()
        month_start = now.replace(day=1).date()
        month_end = month_start + relativedelta(months=1) - timedelta(days=1)

        budgets = Budget.objects.filter(user=request.user)
        budget_data = []

        for budget in budgets:
            # Get expenses for this category this month
            spent = (
                Expense.objects.filter(
                    user=request.user,
                    category=budget.category,
                    date__gte=month_start,
                    date__lte=month_end,
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            budget_data.append(
                {
                    "category": budget.category.name,
                    "spent": float(spent),
                    "budget": float(budget.amount),
                    "percentage": round((spent / budget.amount) * 100, 1)
                    if budget.amount > 0
                    else 0,
                }
            )

        return JsonResponse({"budgets": budget_data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def top_categories_data(request):
    """
    Get top spending destinations with period filtering
    """
    try:
        # Get period parameter from request
        period = request.GET.get("period", "30d")

        # Calculate date range based on period
        end_date = timezone.now().date()

        if period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "3m":
            start_date = end_date - relativedelta(months=3)
        elif period == "6m":
            start_date = end_date - relativedelta(months=6)
        elif period == "1y":
            start_date = end_date - relativedelta(years=1)
        elif period == "all":
            start_date = None
        else:
            # Default to 30 days
            start_date = end_date - timedelta(days=30)

        # Use PostgresClient to get expense data
        pg_client = PostgresClient()
        expense_df = pg_client.get_expense_df(request.user.pk)

        if expense_df.empty:
            return JsonResponse({"categories": []})

        # Filter by date range if not 'all'
        # Filter by date range
        expense_df["date"] = pd.to_datetime(expense_df["date"]).dt.date
        if start_date is not None:
            expense_df = expense_df[
                (expense_df["date"] >= start_date) & (expense_df["date"] <= end_date)
            ]

        # Group and aggregate
        grouped = (
            expense_df.groupby("category_name")
            .agg(amount_sum=("amount", "sum"), transaction_count=("amount", "count"))
            .reset_index()
        )

        # Sort and select top 5
        top_categories = grouped.sort_values("amount_sum", ascending=False).head(5)

        # Prepare response
        categories = [
            {
                "name": row["category_name"],
                "amount": float(row["amount_sum"]),
                "transactions": int(row["transaction_count"]),
                "category": row["category_name"],
            }
            for _, row in top_categories.iterrows()
        ]

        return JsonResponse({"categories": categories})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def expense_years(request):
    # .dates returns list of datetime objects
    date_list = Expense.objects.filter(user=request.user).dates(
        "date", "year", order="DESC"
    )
    years = [d.year for d in date_list]  # Extract year from datetime.date
    return JsonResponse({"years": years})
