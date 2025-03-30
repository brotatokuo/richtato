from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta
from loguru import logger

from richtato.apps.richtato_user.models import User


def _get_line_graph_data(user: User, months: int, model) -> dict:
    # Set the timezone to US/Pacific
    pst = pytz.timezone("US/Pacific")
    today = datetime.now(pst)

    start_date = today - relativedelta(months=months)
    start_date = start_date.replace(day=1)
    logger.debug(f"Start date for line graph: {start_date}")

    months_range = []
    current_month = start_date
    while current_month <= today:
        months_range.append(current_month.strftime("%b %Y"))
        current_month += relativedelta(months=1)

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
    return chart_data
    return chart_data
