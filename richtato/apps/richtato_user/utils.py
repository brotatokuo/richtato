from datetime import datetime

import pytz
from apps.richtato_user.models import User
from dateutil.relativedelta import relativedelta


def _get_line_graph_data(
    user: User, months: int, model, label: str, color: str
) -> dict:
    pst = pytz.timezone("US/Pacific")
    today = datetime.now(pst)
    start_date = today - relativedelta(months=months)
    start_date = start_date.replace(day=1)

    # Query the model (either Income or Expense)
    items = model.objects.filter(
        user=user,
        date__gte=start_date,
    ).order_by("date")

    line_graph_data = {}
    for item in items:
        month_year = item.date.strftime("%b %Y")
        if month_year not in line_graph_data:
            line_graph_data[month_year] = 0
        line_graph_data[month_year] += item.amount

    labels = list(line_graph_data.keys())
    data = list(line_graph_data.values())

    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": label,
                "data": data,
                "borderColor": color,
                "fill": False,
                "tension": 0.4,
            }
        ],
    }

    return chart_data
