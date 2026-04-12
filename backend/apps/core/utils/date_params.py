"""Shared date parameter parsing for views."""

import calendar
from datetime import date
from typing import Optional, Tuple


def parse_date_range_params(
    request_params: dict,
    infer_month_bounds: bool = False,
) -> Tuple[Optional[date], Optional[date]]:
    """Parse start_date and end_date from request query params.

    Accepts ISO-format strings (YYYY-MM-DD).

    When *infer_month_bounds* is True and only one bound is provided, the
    missing bound is inferred to cover the full month of the supplied date.

    Returns (start_date, end_date) — either or both may be None if the params
    are absent.

    Raises ValueError on malformed date strings.
    """
    start_date_str = request_params.get("start_date")
    end_date_str = request_params.get("end_date")

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    if not start_date_str and not end_date_str:
        return None, None

    if start_date_str:
        y, m, d = map(int, start_date_str.split("-"))
        start_date = date(y, m, d)
    if end_date_str:
        y, m, d = map(int, end_date_str.split("-"))
        end_date = date(y, m, d)

    if infer_month_bounds:
        if start_date and not end_date:
            end_date = date(
                start_date.year,
                start_date.month,
                calendar.monthrange(start_date.year, start_date.month)[1],
            )
        if end_date and not start_date:
            start_date = date(end_date.year, end_date.month, 1)

    return start_date, end_date
