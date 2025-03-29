from datetime import datetime

import pytz
from apps.richtato_user.models import User
from dateutil.relativedelta import relativedelta


def _get_line_graph_data(user: User, months: int, model) -> dict:
    # Set the timezone to US/Pacific
    pst = pytz.timezone("US/Pacific")
    today = datetime.now(pst)

    # Calculate the start date for the last 'months' months
    start_date = today - relativedelta(months=months)
    start_date = start_date.replace(day=1)  # Make sure it's the first day of the month

    # Query the model (either Income or Expense)
    items = model.objects.filter(
        user=user,
        date__gte=start_date,  # Filter for items from the start_date onwards
    ).order_by("date")  # Order by date in chronological order

    line_graph_data = {}
    for item in items:
        # Use the month and year as the key (e.g., "Jan 2025")
        month_year = item.date.strftime("%b %Y")
        if month_year not in line_graph_data:
            line_graph_data[month_year] = 0
        line_graph_data[month_year] += item.amount

    # Sort by year first and then month
    sorted_labels = sorted(
        line_graph_data.keys(), key=lambda x: datetime.strptime(x, "%b %Y")
    )  # Sorting by datetime

    # Now, we can create the 'data' list based on the sorted labels
    sorted_data = [line_graph_data[label] for label in sorted_labels]

    chart_data = {
        "labels": sorted_labels,
        "values": sorted_data,
    }

    return chart_data
