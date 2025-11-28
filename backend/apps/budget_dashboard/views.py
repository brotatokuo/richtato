"""
Budget Dashboard views - Thin HTTP wrappers delegating to service layer.

Following clean architecture: Views handle only HTTP concerns.
Business logic is in services, database access is in repositories.
"""

import calendar
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from loguru import logger

from .repositories import BudgetDashboardRepository
from .services import BudgetDashboardService


@login_required
def expense_categories_data(request):
    """Get expense breakdown by category - delegates to service layer."""
    try:
        # Extract parameters
        start_date_param = request.GET.get("start_date")
        end_date_param = request.GET.get("end_date")
        year = request.GET.get("year")
        month = request.GET.get("month")

        # Parse dates if provided
        start_date = None
        end_date = None
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

        # Parse year/month if provided
        year_int = int(year) if year else None
        month_int = int(month) if month else None

        # Inject dependencies and delegate to service
        repo = BudgetDashboardRepository()
        service = BudgetDashboardService(repo)

        # Delegate to service
        data = service.get_expense_categories_data(
            request.user, start_date, end_date, year_int, month_int
        )
        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in expense_categories_data: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def budget_progress(request):
    """Get budget progress for a date range - delegates to service layer."""
    today = date.today()
    year_param = request.GET.get("year")
    month_param = request.GET.get("month")
    start_date_param = request.GET.get("start_date")
    end_date_param = request.GET.get("end_date")

    start_date = None
    end_date = None
    year = today.year
    month = today.month

    # Parse date parameters
    if start_date_param or end_date_param:
        try:
            if start_date_param:
                y, m, d = map(int, start_date_param.split("-"))
                start_date = date(y, m, d)
            if end_date_param:
                y2, m2, d2 = map(int, end_date_param.split("-"))
                end_date = date(y2, m2, d2)
        except Exception:
            return JsonResponse({"error": "Invalid start_date or end_date"}, status=400)

        if start_date and not end_date:
            end_date = date(
                start_date.year,
                start_date.month,
                calendar.monthrange(start_date.year, start_date.month)[1],
            )
        if end_date and not start_date:
            start_date = date(end_date.year, end_date.month, 1)

        if start_date:
            year = start_date.year
            month = start_date.month
    else:
        try:
            year = int(year_param) if year_param else today.year
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid year"}, status=400)

        month_val = None
        if month_param:
            try:
                mnum = int(month_param)
                if 1 <= mnum <= 12:
                    month_val = mnum
            except ValueError:
                key = month_param.strip().lower()
                abbr_map = {
                    m.lower(): i for i, m in enumerate(calendar.month_abbr) if m
                }
                name_map = {
                    m.lower(): i for i, m in enumerate(calendar.month_name) if m
                }
                month_val = abbr_map.get(key) or name_map.get(key)
        else:
            month_val = today.month

        if not month_val:
            return JsonResponse({"error": "Invalid month"}, status=400)

        month = month_val
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])

    # Inject dependencies and delegate to service
    repo = BudgetDashboardRepository()
    service = BudgetDashboardService(repo)

    # Delegate to service
    result = service.get_budget_progress(
        request.user, year, month, start_date, end_date
    )

    return JsonResponse(result)


@login_required
def budget_rankings(request):
    """Get budget rankings - delegates to service layer."""
    try:
        # Extract parameters
        count_param = request.GET.get("count", None)
        count = int(count_param) if count_param else None

        import pytz
        from datetime import datetime

        utc = pytz.timezone("UTC")
        year = int(request.GET.get("year", datetime.now(utc).year))
        month_abbr = request.GET.get("month", datetime.now(utc).strftime("%b"))

        # Parse month
        month_map = {
            month: index for index, month in enumerate(calendar.month_abbr) if month
        }
        month = month_map.get(month_abbr)
        if not month:
            return JsonResponse({"error": "Invalid month"}, status=400)

        logger.debug(f"Year: {year}, Month: {month}")

        # Inject dependencies and delegate to service
        repo = BudgetDashboardRepository()
        service = BudgetDashboardService(repo)

        # Delegate to service
        category_data = service.get_budget_rankings(request.user, year, month, count)

        return JsonResponse({"category_rankings": category_data})

    except Exception as e:
        logger.error(f"Error in budget_rankings: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def expense_years(request):
    """Get list of years with expenses - delegates to service layer."""
    try:
        # Inject dependencies and delegate to service
        repo = BudgetDashboardRepository()
        service = BudgetDashboardService(repo)

        # Delegate to service
        years = service.get_expense_years(request.user)
        return JsonResponse({"years": years})

    except Exception as e:
        logger.error(f"Error in expense_years: {e}")
        return JsonResponse({"error": str(e)}, status=500)
