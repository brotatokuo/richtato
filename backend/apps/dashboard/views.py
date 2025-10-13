from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd
from apps.account.models import Account, AccountTransaction
from apps.budget.models import Budget
from apps.expense.models import Expense
from apps.expense.utils import sankey_cash_flow_overview
from apps.income.models import Income
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from loguru import logger
from utilities.postgres.pg_client import PostgresClient
from utilities.tools import format_currency


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
            )

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
        # Get date range from query params (prefer start_date/end_date)
        import calendar
        from datetime import date

        start_date_param = request.GET.get("start_date")
        end_date_param = request.GET.get("end_date")
        year = request.GET.get("year")
        month = request.GET.get("month")
        today = timezone.now().date()

        start_date: date | None = None
        end_date: date | None = None

        if start_date_param or end_date_param:
            try:
                if start_date_param:
                    y, m, d = map(int, start_date_param.split("-"))
                    start_date = date(y, m, d)
                if end_date_param:
                    y2, m2, d2 = map(int, end_date_param.split("-"))
                    end_date = date(y2, m2, d2)
            except Exception:
                return JsonResponse(
                    {"error": "Invalid start_date or end_date"}, status=400
                )

            if start_date and not end_date:
                end_date = date(
                    start_date.year,
                    start_date.month,
                    calendar.monthrange(start_date.year, start_date.month)[1],
                )
            if end_date and not start_date:
                start_date = date(end_date.year, end_date.month, 1)
        elif year and month:
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
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
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
        # Optional explicit date range
        start_date_param = request.GET.get("start_date")
        end_date_param = request.GET.get("end_date")

        if start_date_param or end_date_param:
            # Parse provided dates; if only one provided, default the other
            if start_date_param:
                start_date = datetime.strptime(start_date_param, "%Y-%m-%d").date()
            else:
                # Default to 6 months prior if only end date given
                tmp_end = datetime.strptime(end_date_param, "%Y-%m-%d").date()
                start_date = (tmp_end - relativedelta(months=6)).replace(day=1)

            if end_date_param:
                end_date = datetime.strptime(end_date_param, "%Y-%m-%d").date()
            else:
                end_date = timezone.now().date()
        else:
            # Default: last 6 months
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
            )

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


def generate_dashboard_context(request: HttpRequest) -> dict:
    logger.debug(f"User {request.user} is authenticated.")
    accounts = Account.objects.filter(user=request.user)
    networth = (
        round(sum(account.latest_balance for account in accounts)) if accounts else 0.0
    )

    # Calculate networth growth percentage
    networth_growth = calculate_networth_growth(request.user)
    # Calculate networth growth CSS class
    networth_growth_class = (
        "positive"
        if networth_growth.startswith("+")
        else "negative"
        if networth_growth.startswith("-")
        else ""
    )

    # Calculate cash flow for the past 30 days
    thirty_days_ago = datetime.now().date() - timedelta(days=30)

    income_30_days = (
        Income.objects.filter(user=request.user, date__gte=thirty_days_ago).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )
    expense_30_days = (
        Expense.objects.filter(user=request.user, date__gte=thirty_days_ago).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    cash_flow_30_days = income_30_days - expense_30_days
    expense_sum = expense_30_days
    income_sum = income_30_days

    # Calculate savings rate based on 30-day cash flow
    if income_30_days > 0:
        savings_rate = round((cash_flow_30_days / income_30_days) * 100, 1)
    else:
        savings_rate = 0

    # Calculate savings rate context
    savings_rate_str = f"{savings_rate}%"
    savings_rate_context, savings_rate_class = calculate_savings_rate_context(
        savings_rate_str
    )

    # Calculate % of non-essential spending for past 30 days
    nonessential_expense = (
        Expense.objects.filter(
            user=request.user,
            category__type="nonessential",
            date__gte=thirty_days_ago,
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    nonessential_spending_pct = (
        round((nonessential_expense / expense_30_days) * 100, 1)
        if expense_30_days > 0
        else 0
    )

    today = datetime.now().date()
    month_start = today.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    budgets = Budget.objects.filter(
        user=request.user, start_date__lte=month_end
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=month_start))

    utilizations = []
    for budget in budgets:
        cat_expense = (
            Expense.objects.filter(
                user=request.user,
                category=budget.category,
                date__gte=thirty_days_ago,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        if budget.amount > 0:
            utilization = (Decimal(cat_expense) / budget.amount) * Decimal(100)
            utilizations.append(float(utilization))

    if utilizations:
        avg_utilization = round(sum(utilizations) / len(utilizations), 1)
        budget_utilization_30_days_str = f"{avg_utilization}%"
    else:
        budget_utilization_30_days_str = "N/A"

    # pg_client = PostgresClient()
    # expense_df = pg_client.get_expense_df(request.user.pk)

    context = {
        "networth": format_currency(networth, 0),
        "networth_growth": networth_growth,
        "networth_growth_class": networth_growth_class,
        "expense_sum": format_currency(expense_sum),
        "income_sum": format_currency(income_sum),
        "budget_utilization_30_days": budget_utilization_30_days_str,
        "savings_rate": savings_rate_str,
        "savings_rate_context": savings_rate_context,
        "savings_rate_class": savings_rate_class,
        "nonessential_spending_pct": nonessential_spending_pct,
    }
    return context


def calculate_networth_growth(user):
    """
    Calculate networth growth percentage for the current month compared to previous month.
    Returns a formatted string like "+5.2% this month" or "-2.1% this month"
    """
    try:
        # Get current date and calculate previous month
        current_date = datetime.now().date()
        current_month_start = current_date.replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)

        # Get current networth (sum of all account latest balances)
        current_accounts = Account.objects.filter(user=user)
        current_networth = (
            sum(account.latest_balance for account in current_accounts)
            if current_accounts
            else 0
        )

        # Get previous month's networth from account transactions
        previous_networth = 0
        for account in current_accounts:
            # Get the latest transaction for this account before the current month
            latest_transaction = (
                AccountTransaction.objects.filter(
                    account=account, date__lt=current_month_start
                )
                .order_by("-date")
                .first()
            )

            if latest_transaction:
                previous_networth += latest_transaction.amount
            else:
                # If no previous transaction, assume balance was 0
                previous_networth += 0

        # Calculate growth percentage
        if previous_networth > 0:
            growth_percentage = (
                (current_networth - previous_networth) / previous_networth
            ) * 100
            growth_percentage = round(growth_percentage, 1)

            # Format the result
            if growth_percentage >= 0:
                return f"+{growth_percentage}% this month"
            else:
                return f"{growth_percentage}% this month"
        else:
            # If no previous networth data, return a default message
            return "New this month"

    except Exception as e:
        logger.error(f"Error calculating networth growth: {e}")
        return "N/A"


def calculate_savings_rate_context(savings_rate):
    """
    Calculate savings rate context based on percentage ranges.
    Returns a tuple of (context_text, css_class)
    """
    try:
        # Extract the numeric value from savings_rate (remove '%' and convert to float)
        rate_value = float(savings_rate.replace("%", ""))

        if rate_value < 10:
            return "Below average", "negative"
        elif rate_value >= 10 and rate_value <= 20:
            return "Average", ""
        elif rate_value > 30:
            return "Above average", "positive"
        else:
            # Between 20-30%
            return "Good", "positive"

    except (ValueError, AttributeError):
        # If we can't parse the savings rate, return a default
        return "N/A", ""


@login_required
def sankey_data(request):
    """API endpoint to return Sankey diagram data as JSON for client-side rendering."""
    try:
        sankey_fig = sankey_cash_flow_overview(request.user.pk)

        # Convert the figure to a dictionary for JSON serialization
        sankey_data = sankey_fig.to_dict()

        return JsonResponse({"success": True, "data": sankey_data})
    except Exception as e:
        logger.error(f"Error generating Sankey data: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to generate Sankey diagram data"},
            status=500,
        )


@login_required
def dashboard_metrics(request):
    """
    Get dashboard metrics (net worth, savings rate, budget utilization, etc.)
    """
    try:
        context = generate_dashboard_context(request)
        return JsonResponse(context)
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return JsonResponse({"error": str(e)}, status=500)
