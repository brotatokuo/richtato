"""
Asset Dashboard views - Thin HTTP wrappers delegating to service layer.

Following clean architecture: Views handle only HTTP concerns.
Business logic is in services, database access is in repositories.
"""

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import JsonResponse
from loguru import logger

from apps.transaction.models import Transaction
from apps.financial_account.models import FinancialAccount

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

        # Build queryset with filters - use Transaction with debit type for expenses
        transactions = Transaction.objects.filter(
            user=request.user, transaction_type="debit"
        )

        if start_date is not None:
            transactions = transactions.filter(date__gte=start_date, date__lte=end_date)

        # Group by category and aggregate
        top_categories = (
            transactions.values("category__name")
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
    Get Sankey diagram data - uses Transaction model for cash flow visualization.
    """
    try:
        from apps.transaction.models import TransactionCategory

        sankey_fig = sankey_cash_flow_overview(request.user)

        # Convert the figure to a dictionary for JSON serialization
        sankey_data_dict = sankey_fig.to_dict()

        return JsonResponse({"success": True, "data": sankey_data_dict})
    except Exception as e:
        logger.error(f"Error generating Sankey data: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to generate Sankey diagram data"},
            status=500,
        )


def sankey_cash_flow_overview(user):
    """
    Create a comprehensive cash flow Sankey diagram showing:
    - Income sources (credit transactions) flowing to account types
    - Account types flowing to expense categories (debit transactions)
    """
    import pandas as pd
    import plotly.graph_objects as go

    # Get data for the last 6 months
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=180)

    # Get user's income data (credit transactions)
    income_data = (
        Transaction.objects.filter(
            user=user,
            transaction_type="credit",
            date__gte=start_date,
            date__lte=end_date,
        )
        .select_related("account")
        .values("description", "amount", "account__account_type")
    )

    # Get user's expense data (debit transactions)
    expense_data = (
        Transaction.objects.filter(
            user=user,
            transaction_type="debit",
            date__gte=start_date,
            date__lte=end_date,
        )
        .select_related("category")
        .values("amount", "category__name")
    )

    # Get user's account balances
    accounts = FinancialAccount.objects.filter(user=user, is_active=True).values(
        "account_type", "balance", "name"
    )

    # Build the Sankey diagram data
    labels = []
    source = []
    target = []
    values = []

    # Step 1: Income sources to account types
    income_df = pd.DataFrame(income_data)
    if not income_df.empty:
        # Merge by both description and account type
        merged_income = (
            income_df.groupby(["description", "account__account_type"])
            .agg({"amount": "sum"})
            .reset_index()
        )

        # Add income source labels
        income_sources = merged_income["description"].unique().tolist()
        for source_name in income_sources:
            labels.append(f"💰 {source_name}")

        # Add account type labels
        account_types = merged_income["account__account_type"].unique().tolist()
        account_type_labels = []
        for acc_type in account_types:
            if acc_type == "savings":
                account_type_labels.append("🏦 Savings")
            elif acc_type == "credit_card":
                account_type_labels.append("💳 Credit Card")
            else:
                account_type_labels.append(
                    f"💳 {str(acc_type).replace('_', ' ').title()}"
                )

        labels.extend(account_type_labels)

        # Create flows from income sources to account types
        for _, row in merged_income.iterrows():
            source_idx = labels.index(f"💰 {row['description']}")

            # Find target account type
            if row["account__account_type"] == "savings":
                target_label = "🏦 Savings"
            elif row["account__account_type"] == "credit_card":
                target_label = "💳 Credit Card"
            else:
                target_label = (
                    f"💳 {str(row['account__account_type']).replace('_', ' ').title()}"
                )

            target_idx = labels.index(target_label)

            source.append(source_idx)
            target.append(target_idx)
            values.append(float(row["amount"]))

    # Step 2: Account types to expense categories
    expense_df = pd.DataFrame(expense_data)
    if not expense_df.empty:
        expense_totals = expense_df.groupby("category__name")["amount"].sum()

        # Add expense category labels
        expense_categories = expense_totals.index.tolist()
        for category in expense_categories:
            if category:
                labels.append(f"📦 {category}")

        # Create flows from checking to expense categories
        checking_label = "💳 Checking"
        if checking_label in labels:
            checking_idx = labels.index(checking_label)

            for category, amount in expense_totals.items():
                if category:
                    category_label = f"📦 {category}"
                    if category_label in labels:
                        category_idx = labels.index(category_label)
                        source.append(checking_idx)
                        target.append(category_idx)
                        values.append(float(amount))

    # Generate colors for links
    link_colors = []
    for i, value in enumerate(values):
        source_label = labels[source[i]] if source else ""

        if "💰" in source_label:
            # Income flows - green
            link_colors.append("rgba(152, 204, 44, 0.8)")
        elif "📦" in labels[target[i]]:
            # Expense flows - red/orange
            link_colors.append("rgba(244, 67, 54, 0.6)")
        else:
            # Default - primary theme green
            link_colors.append("rgba(152, 204, 44, 0.8)")

    # Create the figure
    fig = go.Figure(
        go.Sankey(
            node=dict(
                label=labels,
                pad=15,
                thickness=20,
                color="#2d2d2d",
                line=dict(color="#98cc2c", width=1.5),
            ),
            link=dict(
                source=source,
                target=target,
                value=values,
                color=link_colors,
                hoverlabel=dict(
                    bgcolor="#2d2d2d",
                    bordercolor="#98cc2c",
                    font=dict(color="#ffffff", family="Open Sans, sans-serif"),
                ),
            ),
        )
    )

    fig.update_layout(
        title_font=dict(
            size=20, color="#ffffff", family="Open Sans, sans-serif", weight="bold"
        ),
        font=dict(size=14, color="#ffffff", family="Open Sans, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        hoverlabel=dict(
            bgcolor="#2d2d2d",
            bordercolor="#98cc2c",
            font=dict(color="#ffffff", family="Open Sans, sans-serif"),
        ),
    )

    return fig
