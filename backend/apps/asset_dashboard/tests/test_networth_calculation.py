"""Integration tests for net worth calculation with real DB."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.asset_dashboard.repositories.asset_dashboard_repository import (
    AssetDashboardRepository,
)
from apps.asset_dashboard.services.asset_dashboard_service import (
    AssetDashboardService,
)
from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.richtato_user.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="nwtest", email="nw@test.com", password="testpass123")


@pytest.fixture
def repo():
    return AssetDashboardRepository()


@pytest.fixture
def service(repo):
    return AssetDashboardService(repo)


@pytest.fixture
def checking(user):
    return FinancialAccount.objects.create(
        user=user,
        name="Checking",
        account_type="checking",
        balance=Decimal("10000.00"),
    )


@pytest.fixture
def savings(user):
    return FinancialAccount.objects.create(
        user=user,
        name="Savings",
        account_type="savings",
        balance=Decimal("25000.00"),
    )


@pytest.fixture
def credit_card(user):
    return FinancialAccount.objects.create(
        user=user,
        name="Chase CC",
        account_type="credit_card",
        balance=Decimal("-3000.00"),
        is_liability=True,
    )


class TestNetWorthCalculation:
    """Net worth = sum of all balances (assets positive, liabilities negative)."""

    def test_assets_only(self, repo, user, checking, savings):
        nw = repo.get_networth(user)
        assert nw == Decimal("35000.00")

    def test_assets_minus_liabilities(self, repo, user, checking, savings, credit_card):
        nw = repo.get_networth(user)
        # 10000 + 25000 + (-3000) = 32000
        assert nw == Decimal("32000.00")

    def test_total_assets(self, repo, user, checking, savings, credit_card):
        assets = repo.get_total_assets(user)
        assert assets == Decimal("35000.00")

    def test_total_liabilities_positive_display(self, repo, user, checking, savings, credit_card):
        liabilities = repo.get_total_liabilities(user)
        # Displayed as positive even though stored negative
        assert liabilities == Decimal("3000.00")

    def test_zero_accounts(self, repo, user):
        nw = repo.get_networth(user)
        assert nw == Decimal("0")

    def test_all_liability_accounts(self, repo, user, credit_card):
        nw = repo.get_networth(user)
        assert nw == Decimal("-3000.00")

    def test_inactive_accounts_excluded(self, repo, user, checking, savings):
        savings.is_active = False
        savings.save()

        nw = repo.get_networth(user)
        assert nw == Decimal("10000.00")


class TestGetBalanceAtDate:
    """get_balance_at_date should use history, not transaction sums."""

    def test_returns_history_balance(self, repo, checking):
        target = date(2025, 6, 1)
        AccountBalanceHistory.objects.create(account=checking, date=target, balance=Decimal("8000.00"))
        result = repo.get_balance_at_date(checking, target)
        assert result == Decimal("8000.00")

    def test_returns_most_recent_before_date(self, repo, checking):
        AccountBalanceHistory.objects.create(account=checking, date=date(2025, 5, 1), balance=Decimal("7000.00"))
        AccountBalanceHistory.objects.create(account=checking, date=date(2025, 5, 15), balance=Decimal("7500.00"))
        result = repo.get_balance_at_date(checking, date(2025, 5, 20))
        assert result == Decimal("7500.00")

    def test_no_history_falls_back_to_current(self, repo, checking):
        result = repo.get_balance_at_date(checking, date(2025, 6, 1))
        assert result == Decimal("10000.00")

    def test_date_before_all_history_falls_back(self, repo, checking):
        AccountBalanceHistory.objects.create(account=checking, date=date(2025, 6, 1), balance=Decimal("9000.00"))
        result = repo.get_balance_at_date(checking, date(2025, 5, 1))
        assert result == Decimal("10000.00")


class TestDashboardMetrics:
    """Integration tests for dashboard metrics endpoint."""

    def test_metrics_include_liabilities_in_networth(self, service, user, checking, credit_card):
        metrics = service.get_dashboard_metrics(user)
        # 10000 + (-3000) = 7000
        assert metrics["networth"] == 7000.0
        assert metrics["total_assets"] == 10000.0
        assert metrics["total_liabilities"] == 3000.0

    def test_metrics_with_no_accounts(self, service, user):
        metrics = service.get_dashboard_metrics(user)
        assert metrics["networth"] == 0.0
        assert metrics["total_assets"] == 0.0
        assert metrics["total_liabilities"] == 0.0


class TestNetWorthGrowth:
    """Net worth growth should include liabilities and use history."""

    def test_growth_with_history(self, service, repo, user, checking, credit_card):
        prev_month_end = date.today().replace(day=1) - timedelta(days=1)
        AccountBalanceHistory.objects.create(account=checking, date=prev_month_end, balance=Decimal("9000.00"))
        AccountBalanceHistory.objects.create(account=credit_card, date=prev_month_end, balance=Decimal("-2000.00"))
        # Previous NW: 9000 + (-2000) = 7000
        # Current NW: 10000 + (-3000) = 7000
        result = service._calculate_networth_growth(user)
        assert "+0.0%" in result or "0.0%" in result

    def test_growth_positive(self, service, repo, user, checking):
        prev_month_end = date.today().replace(day=1) - timedelta(days=1)
        AccountBalanceHistory.objects.create(account=checking, date=prev_month_end, balance=Decimal("8000.00"))
        result = service._calculate_networth_growth(user)
        assert result.startswith("+")
        assert "this month" in result

    def test_growth_negative(self, service, repo, user, checking):
        prev_month_end = date.today().replace(day=1) - timedelta(days=1)
        AccountBalanceHistory.objects.create(account=checking, date=prev_month_end, balance=Decimal("15000.00"))
        result = service._calculate_networth_growth(user)
        assert result.startswith("-")

    def test_growth_no_history(self, service, repo, user, checking):
        result = service._calculate_networth_growth(user)
        # No previous history → should show growth based on fallback
        assert "this month" in result or result == "New this month"
