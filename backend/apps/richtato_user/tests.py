from datetime import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.test import TestCase

from richtato.apps.account.models import Account, AccountTransaction
from richtato.apps.richtato_user.views import (
    calculate_networth_growth,
    calculate_savings_rate_context,
)

User = get_user_model()


class NetworthGrowthTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Create a test account
        self.account = Account.objects.create(
            user=self.user,
            type="checking",
            asset_entity_name="chase",
            name="Test Checking Account",
            latest_balance=Decimal("10000.00"),
            latest_balance_date=datetime.now().date(),
        )

    def test_networth_growth_calculation(self):
        """Test networth growth calculation with sample data"""

        # Create a transaction from last month
        last_month = datetime.now().date() - relativedelta(months=1)
        AccountTransaction.objects.create(
            account=self.account, amount=Decimal("8000.00"), date=last_month
        )

        # Calculate growth
        growth = calculate_networth_growth(self.user)

        # Should show positive growth since current balance (10000) > previous (8000)
        self.assertIn("+", growth)
        self.assertIn("%", growth)
        self.assertIn("this month", growth)

    def test_networth_growth_no_previous_data(self):
        """Test networth growth when no previous data exists"""

        # No previous transactions
        growth = calculate_networth_growth(self.user)

        # Should return "New this month" for new accounts
        self.assertEqual(growth, "New this month")

    def test_networth_growth_negative(self):
        """Test networth growth when balance decreased"""

        # Set current balance lower than previous
        self.account.latest_balance = Decimal("6000.00")
        self.account.save()

        # Create a transaction from last month with higher balance
        last_month = datetime.now().date() - relativedelta(months=1)
        AccountTransaction.objects.create(
            account=self.account, amount=Decimal("8000.00"), date=last_month
        )

        # Calculate growth
        growth = calculate_networth_growth(self.user)

        # Should show negative growth
        self.assertIn("-", growth)
        self.assertIn("%", growth)
        self.assertIn("this month", growth)


class SavingsRateContextTestCase(TestCase):
    def test_savings_rate_context_below_average(self):
        """Test savings rate context for below average rates"""
        context, css_class = calculate_savings_rate_context("5%")
        self.assertEqual(context, "Below average")
        self.assertEqual(css_class, "negative")

        context, css_class = calculate_savings_rate_context("9.9%")
        self.assertEqual(context, "Below average")
        self.assertEqual(css_class, "negative")

    def test_savings_rate_context_average(self):
        """Test savings rate context for average rates"""
        context, css_class = calculate_savings_rate_context("10%")
        self.assertEqual(context, "Average")
        self.assertEqual(css_class, "")

        context, css_class = calculate_savings_rate_context("15%")
        self.assertEqual(context, "Average")
        self.assertEqual(css_class, "")

        context, css_class = calculate_savings_rate_context("20%")
        self.assertEqual(context, "Average")
        self.assertEqual(css_class, "")

    def test_savings_rate_context_good(self):
        """Test savings rate context for good rates (20-30%)"""
        context, css_class = calculate_savings_rate_context("25%")
        self.assertEqual(context, "Good")
        self.assertEqual(css_class, "positive")

        context, css_class = calculate_savings_rate_context("30%")
        self.assertEqual(context, "Good")
        self.assertEqual(css_class, "positive")

    def test_savings_rate_context_above_average(self):
        """Test savings rate context for above average rates"""
        context, css_class = calculate_savings_rate_context("31%")
        self.assertEqual(context, "Above average")
        self.assertEqual(css_class, "positive")

        context, css_class = calculate_savings_rate_context("50%")
        self.assertEqual(context, "Above average")
        self.assertEqual(css_class, "positive")

    def test_savings_rate_context_invalid_input(self):
        """Test savings rate context with invalid input"""
        context, css_class = calculate_savings_rate_context("invalid")
        self.assertEqual(context, "N/A")
        self.assertEqual(css_class, "")
