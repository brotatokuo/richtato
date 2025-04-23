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
    logger.debug(type(current_month))
    logger.debug(type(today))

    while current_month <= today:
        months_range.append(current_month.strftime("%b %Y"))
        current_month += relativedelta(months=1)

    # Query items - if months is None, we'll use the calculated start_date from earliest record
    items = model.objects.filter(
        user=user,
        date__gte=start_date,
    ).order_by("date")

    logger.debug(
        f"Model {model.__name__}, User {user}, Start date {start_date}, Items: {items}"
    )

    line_graph_data = {month: 0 for month in months_range}
    logger.debug(f"Initial line graph data: {line_graph_data}")

    for item in items:
        month_year = item.date.strftime("%b %Y")
        if month_year in line_graph_data:
            line_graph_data[month_year] += item.amount
    logger.debug(f"Line graph data after aggregation: {line_graph_data}")

    sorted_labels = list(months_range)
    sorted_data = [line_graph_data[label] for label in sorted_labels]

    chart_data = {
        "labels": sorted_labels,
        "values": sorted_data,
    }

    logger.debug(f"Final chart data: {chart_data}")

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
