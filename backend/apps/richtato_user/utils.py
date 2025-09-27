from datetime import datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta
from loguru import logger

from richtato.apps.expense.models import Expense
from richtato.apps.income.models import Income
from richtato.apps.richtato_user.models import User

# Set the timezone to US/Pacific
pst = pytz.timezone("US/Pacific")
today = datetime.now(pst).date()


def _get_line_graph_data_by_month(
    user: User, model: type[Expense] | type[Income]
) -> dict:
    earliest_record = model.objects.filter(user=user).order_by("date").first()
    if earliest_record:
        start_date = earliest_record.date.replace(day=1)
    else:
        # If no records, use today as start date
        start_date = today.replace(day=1)

    logger.debug(f"Start date for line graph: {start_date}")

    # Generate months range from start date to today
    months_range = []
    current_month = start_date

    while current_month <= today:
        months_range.append(current_month.strftime("%b %Y"))
        current_month += relativedelta(months=1)

    # Query items - if months is None, we'll use the calculated start_date from earliest record
    items = model.objects.filter(
        user=user,
        date__gte=start_date,
    ).order_by("date")

    line_graph_data = {month: 0 for month in months_range}

    for item in items:
        month_year = item.date.strftime("%b %Y")
        if month_year in line_graph_data:
            line_graph_data[month_year] += item.amount

    sorted_labels = list(months_range)
    sorted_data = [line_graph_data[label] for label in sorted_labels]

    chart_data = {
        "labels": sorted_labels,
        "values": sorted_data,
    }

    return chart_data


def _get_line_graph_data_by_day(
    user: User, model: type[Expense] | type[Income]
) -> dict:
    start_date = today - timedelta(
        days=29
    )  # Include today + 29 previous days = 30 days

    logger.debug(f"Start date for daily graph: {start_date}")

    # Generate daily range
    days_range = [(start_date + timedelta(days=i)) for i in range(30)]
    formatted_days = [day.strftime("%b %d") for day in days_range]

    # Query items within the last 30 days
    items = model.objects.filter(user=user, date__range=(start_date, today)).order_by(
        "date"
    )

    line_graph_data = {day.strftime("%b %d"): 0 for day in days_range}

    for item in items:
        day_label = item.date.strftime("%b %d")
        if day_label in line_graph_data:
            line_graph_data[day_label] += item.amount

    chart_data = {
        "labels": formatted_days,
        "values": [line_graph_data[day] for day in formatted_days],
    }

    return chart_data


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
        from richtato.apps.account.models import Account, AccountTransaction

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


def generate_dashboard_context(request):
    from decimal import Decimal

    from django.db.models import Q, Sum

    from richtato.apps.account.models import Account
    from richtato.apps.budget.models import Budget
    from richtato.apps.expense.models import Expense
    from richtato.apps.income.models import Income
    from richtato.utilities.tools import format_currency

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
