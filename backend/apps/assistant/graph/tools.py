"""LangGraph tools that wrap existing service layer methods.

Each tool receives the user from the RunnableConfig's configurable dict,
keeping the same auth boundary as the REST API views.
"""

import json
from datetime import date
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool


def _get_user(config: RunnableConfig):
    """Extract user from LangGraph config."""
    return config["configurable"]["user"]


@tool
def get_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category_name: Optional[str] = None,
    account_name: Optional[str] = None,
    transaction_type: Optional[str] = None,
    limit: int = 25,
    *,
    config: RunnableConfig,
) -> str:
    """Fetch the user's transactions with optional filters.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        category_name: Filter by category name (case-insensitive partial match).
        account_name: Filter by account name (case-insensitive partial match).
        transaction_type: Filter by 'debit' (expenses) or 'credit' (income).
        limit: Max number of transactions to return (default 25).
    """
    from apps.financial_account.models import FinancialAccount
    from apps.transaction.models import TransactionCategory
    from apps.transaction.services.transaction_service import TransactionService

    user = _get_user(config)
    svc = TransactionService()

    parsed_start = date.fromisoformat(start_date) if start_date else None
    parsed_end = date.fromisoformat(end_date) if end_date else None

    account = None
    if account_name:
        account = FinancialAccount.objects.filter(
            user=user, name__icontains=account_name, is_active=True
        ).first()

    category = None
    if category_name:
        category = TransactionCategory.objects.filter(
            user=user, name__icontains=category_name, is_enabled=True
        ).first()

    qs = svc.get_user_transactions(
        user=user,
        start_date=parsed_start,
        end_date=parsed_end,
        account=account,
        category=category,
        transaction_type=transaction_type,
    )[:limit]

    results = []
    for txn in qs:
        results.append({
            "date": str(txn.date),
            "description": txn.description,
            "amount": float(txn.amount),
            "type": txn.transaction_type,
            "category": txn.category.name if txn.category else "Uncategorized",
            "account": txn.account.name if txn.account else "Unknown",
        })

    return json.dumps({"transactions": results, "count": len(results)})


@tool
def search_transactions(
    search_term: str,
    limit: int = 20,
    *,
    config: RunnableConfig,
) -> str:
    """Search transactions by description keyword.

    Args:
        search_term: Keyword to search for in transaction descriptions.
        limit: Max results to return (default 20).
    """
    from apps.transaction.services.transaction_service import TransactionService

    user = _get_user(config)
    svc = TransactionService()
    txns = svc.search_transactions(user, search_term, limit)

    results = []
    for txn in txns:
        results.append({
            "date": str(txn.date),
            "description": txn.description,
            "amount": float(txn.amount),
            "type": txn.transaction_type,
            "category": txn.category.name if txn.category else "Uncategorized",
            "account": txn.account.name if txn.account else "Unknown",
        })

    return json.dumps({"transactions": results, "count": len(results)})


@tool
def get_transaction_summary(
    start_date: str,
    end_date: str,
    *,
    config: RunnableConfig,
) -> str:
    """Get a summary of transactions for a date range including totals by category.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
    """
    from apps.transaction.services.transaction_service import TransactionService

    user = _get_user(config)
    svc = TransactionService()

    summary = svc.get_transaction_summary(
        user,
        date.fromisoformat(start_date),
        date.fromisoformat(end_date),
    )

    serializable = {
        "total_transactions": summary["total_transactions"],
        "total_income": float(summary["total_income"]),
        "total_expenses": float(summary["total_expenses"]),
        "net": float(summary["net"]),
        "by_category": {
            k: {"count": v["count"], "total": float(v["total"])}
            for k, v in summary["by_category"].items()
        },
    }
    return json.dumps(serializable)


@tool
def get_cashflow_summary(
    start_date: str,
    end_date: str,
    *,
    config: RunnableConfig,
) -> str:
    """Get cashflow breakdown showing income, expenses, and investments by category.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
    """
    from apps.transaction.services.transaction_service import TransactionService

    user = _get_user(config)
    svc = TransactionService()

    data = svc.get_cashflow_summary(
        user,
        date.fromisoformat(start_date),
        date.fromisoformat(end_date),
    )
    return json.dumps(data)


@tool
def get_account_summary(*, config: RunnableConfig) -> str:
    """Get a summary of all the user's financial accounts with balances grouped by type."""
    from apps.financial_account.services.account_service import AccountService

    user = _get_user(config)
    svc = AccountService()
    accounts = svc.get_user_accounts(user, active_only=True)

    account_list = []
    for acc in accounts:
        account_list.append({
            "name": acc.name,
            "type": acc.account_type,
            "balance": float(acc.balance),
            "currency": acc.currency,
            "is_liability": acc.is_liability,
            "institution": acc.institution.name if acc.institution else None,
        })

    summary = svc.get_account_summary(user)
    serializable_summary = {
        "total_accounts": summary["total_accounts"],
        "checking": {
            "count": summary["checking"]["count"],
            "total_balance": float(summary["checking"]["total_balance"]),
        },
        "savings": {
            "count": summary["savings"]["count"],
            "total_balance": float(summary["savings"]["total_balance"]),
        },
        "credit_card": {
            "count": summary["credit_card"]["count"],
            "total_balance": float(summary["credit_card"]["total_balance"]),
        },
    }

    return json.dumps({"accounts": account_list, "summary": serializable_summary})


@tool
def get_budget_progress(*, config: RunnableConfig) -> str:
    """Get the current active budget's progress showing allocated vs spent for each category."""
    from apps.budget.services.budget_calculation_service import (
        BudgetCalculationService,
    )
    from apps.budget.services.budget_service import BudgetService

    user = _get_user(config)
    budget_svc = BudgetService()
    calc_svc = BudgetCalculationService()

    budget = budget_svc.get_current_budget(user)
    if not budget:
        return json.dumps({"error": "No active budget found."})

    progress = calc_svc.calculate_budget_progress(budget)

    serializable = {
        "budget_name": progress["budget_name"],
        "period": progress["period"],
        "totals": {
            "allocated": float(progress["totals"]["allocated"]),
            "spent": float(progress["totals"]["spent"]),
            "remaining": float(progress["totals"]["remaining"]),
            "percentage_used": float(progress["totals"]["percentage_used"]),
        },
        "categories": [
            {
                "name": cat["category"]["name"],
                "allocated": float(cat["allocated_amount"]),
                "spent": float(cat["spent_amount"]),
                "remaining": float(cat["remaining_amount"]),
                "percentage_used": cat["percentage_used"],
                "status": cat["status"],
            }
            for cat in progress["categories"]
        ],
    }
    return json.dumps(serializable)


@tool
def get_net_worth_metrics(*, config: RunnableConfig) -> str:
    """Get dashboard metrics: net worth, total assets, total liabilities, 30-day income/expenses, and savings rate."""
    from apps.asset_dashboard.repositories import AssetDashboardRepository
    from apps.asset_dashboard.services import AssetDashboardService

    user = _get_user(config)
    repo = AssetDashboardRepository()
    svc = AssetDashboardService(repo)

    return json.dumps(svc.get_dashboard_metrics(user))


@tool
def get_spending_by_category(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    *,
    config: RunnableConfig,
) -> str:
    """Get expense breakdown by category for a date range (pie chart data).

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        year: Year (used if start_date/end_date not provided).
        month: Month 1-12 (used if start_date/end_date not provided).
    """
    from apps.budget_dashboard.repositories import BudgetDashboardRepository
    from apps.budget_dashboard.services import BudgetDashboardService

    user = _get_user(config)
    repo = BudgetDashboardRepository()
    svc = BudgetDashboardService(repo)

    parsed_start = date.fromisoformat(start_date) if start_date else None
    parsed_end = date.fromisoformat(end_date) if end_date else None

    data = svc.get_expense_categories_data(
        user,
        start_date=parsed_start,
        end_date=parsed_end,
        year=year,
        month=month,
    )

    return json.dumps({
        "categories": [
            {"name": label, "amount": amount}
            for label, amount in zip(data["labels"], data["datasets"][0]["data"])
        ],
        "start_date": data["start_date"],
        "end_date": data["end_date"],
    })


@tool
def get_income_vs_expenses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    *,
    config: RunnableConfig,
) -> str:
    """Get monthly income vs expenses comparison over time.

    Args:
        start_date: Start date in YYYY-MM-DD format (defaults to 6 months ago).
        end_date: End date in YYYY-MM-DD format (defaults to today).
    """
    from apps.asset_dashboard.repositories import AssetDashboardRepository
    from apps.asset_dashboard.services import AssetDashboardService

    user = _get_user(config)
    repo = AssetDashboardRepository()
    svc = AssetDashboardService(repo)

    parsed_start = date.fromisoformat(start_date) if start_date else None
    parsed_end = date.fromisoformat(end_date) if end_date else None

    data = svc.get_income_expenses_data(user, parsed_start, parsed_end)

    months = []
    income_dataset = data["datasets"][0]["data"]
    expense_dataset = data["datasets"][1]["data"]
    for i, label in enumerate(data["labels"]):
        months.append({
            "month": label,
            "income": income_dataset[i],
            "expenses": expense_dataset[i],
            "net": income_dataset[i] - expense_dataset[i],
        })

    return json.dumps({"months": months})


@tool
def get_networth_history(
    period: str = "6m",
    *,
    config: RunnableConfig,
) -> str:
    """Get net worth history over time.

    Args:
        period: Time period - '1m', '3m', '6m', '1y', or 'all'.
    """
    from apps.asset_dashboard.repositories import AssetDashboardRepository
    from apps.asset_dashboard.services import AssetDashboardService

    user = _get_user(config)
    repo = AssetDashboardRepository()
    svc = AssetDashboardService(repo)

    data = svc.get_networth_history(user, period)
    return json.dumps(data)


ALL_TOOLS = [
    get_transactions,
    search_transactions,
    get_transaction_summary,
    get_cashflow_summary,
    get_account_summary,
    get_budget_progress,
    get_net_worth_metrics,
    get_spending_by_category,
    get_income_vs_expenses,
    get_networth_history,
]
