from datetime import datetime

import pytz
from apps.richtato_user.models import User
from dateutil.relativedelta import relativedelta
from loguru import logger


def _get_line_graph_data(user: User, months: int, model) -> dict:
    # Set the timezone to US/Pacific
    pst = pytz.timezone("US/Pacific")
    today = datetime.now(pst)

    # Calculate the start date for the last 'months' months (inclusive of this month)
    start_date = today - relativedelta(months=months)
    start_date = start_date.replace(day=1)  # Make sure it's the first day of the month
    logger.debug(f"Start date for line graph: {start_date}")
    # Generate a list of months in the date range (from start_date to today)
    months_range = []
    current_month = start_date
    while current_month <= today:
        months_range.append(current_month.strftime("%b %Y"))
        current_month += relativedelta(months=1)

    # Query the model (either Income or Expense) for items in the given range
    items = model.objects.filter(
        user=user,
        date__gte=start_date,  # Filter for items from the start_date onwards
    ).order_by("date")  # Order by date in chronological order

    logger.debug(f"Model {model.__name__}, User {user}, items:", items)

    # Initialize a dictionary to store the amounts for each month
    line_graph_data = {month: 0 for month in months_range}  # Start with all months having 0

    # Populate the data with the actual amounts from the database
    for item in items:
        # Use the month and year as the key (e.g., "Jan 2025")
        month_year = item.date.strftime("%b %Y")
        if month_year in line_graph_data:
            line_graph_data[month_year] += item.amount

    # Prepare the final chart data
    sorted_labels = list(months_range)  # Ensure the order is correct
    sorted_data = [line_graph_data[label] for label in sorted_labels]

    chart_data = {
        "labels": sorted_labels,
        "values": sorted_data,
    }

    return chart_data