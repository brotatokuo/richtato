"""
Asset Dashboard views - Thin HTTP wrappers delegating to service layer.

Following clean architecture: Views handle only HTTP concerns.
Business logic is in services, database access is in repositories.
"""

from datetime import datetime

from apps.expense.utils import sankey_cash_flow_overview
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from loguru import logger

from .repositories import AssetDashboardRepository
from .services import AssetDashboardService


@login_required
def cash_flow_data(request):
    """Get cash flow data - delegates to service layer."""
    try:
        # Extract parameters
        period = request.GET.get("period", "6m")

        # Inject dependencies and delegate to service
        repo = AssetDashboardRepository()
        service = AssetDashboardService(repo)

        # Delegate to service
        data = service.get_cash_flow_data(request.user, period)
        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in cash_flow_data: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def income_expenses_data(request):
    """Get monthly income vs expenses comparison - delegates to service layer."""
    try:
        # Extract optional date parameters
        start_date_param = request.GET.get("start_date")
        end_date_param = request.GET.get("end_date")

        start_date = None
        end_date = None
        if start_date_param:
            start_date = datetime.strptime(start_date_param, "%Y-%m-%d").date()
        if end_date_param:
            end_date = datetime.strptime(end_date_param, "%Y-%m-%d").date()

        # Inject dependencies and delegate to service
        repo = AssetDashboardRepository()
        service = AssetDashboardService(repo)

        # Delegate to service
        data = service.get_income_expenses_data(request.user, start_date, end_date)
        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in income_expenses_data: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def savings_data(request):
    """Get savings accumulation data - delegates to service layer."""
    try:
        # Inject dependencies and delegate to service
        repo = AssetDashboardRepository()
        service = AssetDashboardService(repo)

        # Delegate to service
        data = service.get_savings_data(request.user)
        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in savings_data: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def dashboard_metrics(request):
    """Get dashboard metrics - delegates to service layer."""
    try:
        # Inject dependencies and delegate to service
        repo = AssetDashboardRepository()
        service = AssetDashboardService(repo)

        # Delegate to service
        context = service.get_dashboard_metrics(request.user)
        return JsonResponse(context)
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def top_categories_data(request):
    """
    Get top spending categories - uses Django ORM for aggregation.
    """
    try:
        # Extract period parameter
        period = request.GET.get("period", "30d")

        # Calculate date range based on period
        from datetime import timedelta

        from apps.expense.models import Expense
        from dateutil.relativedelta import relativedelta
        from django.db.models import Count, Sum

        end_date = datetime.now().date()

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

        # Build queryset with filters
        expenses = Expense.objects.filter(user=request.user)

        if start_date is not None:
            expenses = expenses.filter(date__gte=start_date, date__lte=end_date)

        # Group by category and aggregate
        top_categories = (
            expenses.values("category__name")
            .annotate(amount_sum=Sum("amount"), transaction_count=Count("id"))
            .order_by("-amount_sum")[:5]
        )

        # Prepare response
        categories = [
            {
                "name": cat["category__name"] or "Uncategorized",
                "amount": float(cat["amount_sum"] or 0),
                "transactions": cat["transaction_count"],
                "category": cat["category__name"] or "Uncategorized",
            }
            for cat in top_categories
        ]

        return JsonResponse({"categories": categories})

    except Exception as e:
        logger.error(f"Error in top_categories_data: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def sankey_data(request):
    """
    Get Sankey diagram data - delegates to expense utils.

    Note: This uses specialized Sankey diagram generation from expense.utils.
    """
    try:
        sankey_fig = sankey_cash_flow_overview(request.user.pk)

        # Convert the figure to a dictionary for JSON serialization
        sankey_data_dict = sankey_fig.to_dict()

        return JsonResponse({"success": True, "data": sankey_data_dict})
    except Exception as e:
        logger.error(f"Error generating Sankey data: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to generate Sankey diagram data"},
            status=500,
        )
