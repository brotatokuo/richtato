import random
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils.text import slugify

from apps.budget.models import Budget, BudgetCategory
from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory


class DemoUserFactory:
    username = "demo"
    email = "demo@richtato.com"
    password = "demopassword123"

    def __init__(self):
        self.user = None
        self.checking_account = None
        self.savings_account = None
        self.credit_card = None
        self.today = date.today()
        self.one_year_ago = self.today - timedelta(days=365)
        self.first_friday = self.get_previous_friday(self.today)

    @transaction.atomic
    def create_or_reset(self):
        self._delete_existing_user()
        self._create_user()
        self._create_financial_accounts()
        self._create_categories()
        self._create_income_transactions()
        self._create_expense_transactions()
        self._create_budgets()
        return self.user

    def get_previous_friday(self, d):
        return d - timedelta(days=(d.weekday() - 4) % 7)

    def _delete_existing_user(self):
        User.objects.filter(username=self.username).delete()

    def _create_user(self):
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            is_demo=False,
        )

    def _create_financial_accounts(self):
        """Create financial accounts for the demo user."""
        # Create institutions
        boa, _ = FinancialInstitution.objects.get_or_create(
            slug="bank-of-america",
            defaults={"name": "Bank of America"},
        )
        chase, _ = FinancialInstitution.objects.get_or_create(
            slug="chase",
            defaults={"name": "Chase"},
        )
        amex, _ = FinancialInstitution.objects.get_or_create(
            slug="american-express",
            defaults={"name": "American Express"},
        )

        # Create accounts
        self.checking_account = FinancialAccount.objects.create(
            user=self.user,
            name="BofA Checking",
            institution=boa,
            account_type="checking",
            balance=Decimal("5000.00"),
        )
        self.savings_account = FinancialAccount.objects.create(
            user=self.user,
            name="Chase Savings",
            institution=chase,
            account_type="savings",
            balance=Decimal("10000.00"),
        )

        # Credit cards
        self.boa_card = FinancialAccount.objects.create(
            user=self.user,
            name="Bank of America Custom Cash",
            institution=boa,
            account_type="credit_card",
            balance=Decimal("0"),
        )
        self.amex_card = FinancialAccount.objects.create(
            user=self.user,
            name="American Express Platinum",
            institution=amex,
            account_type="credit_card",
            balance=Decimal("0"),
        )
        self.chase_card = FinancialAccount.objects.create(
            user=self.user,
            name="Chase Sapphire Preferred",
            institution=chase,
            account_type="credit_card",
            balance=Decimal("0"),
        )

    def _create_categories(self):
        """Create transaction categories for the demo user."""
        categories_data = [
            ("Travel", "travel", "✈️", "#3B82F6", False, True),
            ("Shopping", "shopping", "🛍️", "#8B5CF6", False, True),
            ("Groceries", "groceries", "🛒", "#10B981", False, True),
            ("Dining", "dining", "🍽️", "#F59E0B", False, True),
            ("Utilities", "utilities", "💡", "#6366F1", False, True),
            ("Housing", "housing", "🏠", "#EC4899", False, True),
            ("Medical", "medical", "🏥", "#EF4444", False, True),
            ("Entertainment", "entertainment", "🎬", "#14B8A6", False, True),
            ("Subscriptions", "subscriptions", "📱", "#F97316", False, True),
            ("Car", "car", "🚗", "#84CC16", False, True),
            ("Salary", "salary", "💰", "#22C55E", True, False),
        ]

        for name, slug, icon, color, is_income, is_expense in categories_data:
            TransactionCategory.objects.create(
                user=self.user,
                name=name,
                slug=slug,
                icon=icon,
                color=color,
                is_income=is_income,
                is_expense=is_expense,
            )

    def _create_income_transactions(self):
        """Create income transactions (credit type)."""
        pay_dates = []
        current_friday = self.first_friday
        while current_friday >= self.one_year_ago:
            pay_dates.append(current_friday)
            current_friday -= timedelta(days=14)
        pay_dates.reverse()

        salary_category = TransactionCategory.objects.get(user=self.user, slug="salary")

        income_entries = []
        for pay_date in pay_dates:
            income_entries.extend(
                [
                    Transaction(
                        user=self.user,
                        account=self.checking_account,
                        description="Bi-weekly Salary",
                        date=pay_date,
                        amount=Decimal("3000.00"),
                        transaction_type="credit",
                        category=salary_category,
                        sync_source="manual",
                    ),
                    Transaction(
                        user=self.user,
                        account=self.savings_account,
                        description="Bi-weekly Salary",
                        date=pay_date,
                        amount=Decimal("500.00"),
                        transaction_type="credit",
                        category=salary_category,
                        sync_source="manual",
                    ),
                ]
            )
        Transaction.objects.bulk_create(income_entries, ignore_conflicts=True)

    def _create_expense_transactions(self):
        """Create expense transactions (debit type)."""
        # Get categories for the demo user
        categories = {
            c.slug: c for c in TransactionCategory.objects.filter(user=self.user)
        }
        travel_category = categories.get("travel")
        shopping_category = categories.get("shopping")
        groceries_category = categories.get("groceries")
        dining_category = categories.get("dining")
        utilities_category = categories.get("utilities")
        housing_category = categories.get("housing")
        medical_category = categories.get("medical")
        entertainment_category = categories.get("entertainment")
        subscriptions_category = categories.get("subscriptions")
        gas_category = categories.get("car")

        # Create a list of realistic expense transactions
        expense_entries = []

        # Generate dates for the past year
        current_date = self.one_year_ago
        while current_date <= self.today:
            # Groceries (weekly)
            if current_date.weekday() == 0:  # Monday
                expense_entries.append(
                    Transaction(
                        user=self.user,
                        account=self.boa_card,
                        category=groceries_category,
                        description="Whole Foods Market",
                        date=current_date,
                        amount=Decimal("120.50"),
                        transaction_type="debit",
                        sync_source="manual",
                    )
                )

            # Gas (every 2 weeks)
            if (
                current_date.weekday() == 2 and current_date.day % 14 < 7
            ):  # Wednesday every 2 weeks
                expense_entries.append(
                    Transaction(
                        user=self.user,
                        account=self.boa_card,
                        category=gas_category,
                        description="Shell Gas Station",
                        date=current_date,
                        amount=Decimal("45.00"),
                        transaction_type="debit",
                        sync_source="manual",
                    )
                )

            # Dining out (randomly 2-3 times per week)
            if (
                current_date.weekday() in [4, 5, 6] and current_date.day % 7 < 3
            ):  # Weekend dining
                restaurants = [
                    ("Chipotle", Decimal("15.75")),
                    ("Starbucks", Decimal("8.50")),
                    ("Pizza Hut", Decimal("25.00")),
                    ("McDonald's", Decimal("12.30")),
                    ("Subway", Decimal("11.25")),
                ]
                restaurant, amount = restaurants[current_date.day % len(restaurants)]
                expense_entries.append(
                    Transaction(
                        user=self.user,
                        account=self.chase_card,
                        category=dining_category,
                        description=restaurant,
                        date=current_date,
                        amount=amount,
                        transaction_type="debit",
                        sync_source="manual",
                    )
                )

            # Shopping (every ~3 days, random amount $50-$200)
            if (current_date - self.one_year_ago).days % 3 == 0:
                shopping_items = [
                    "Amazon.com",
                    "Target",
                    "Walmart",
                    "Best Buy",
                    "eBay",
                    "Macy's",
                    "Costco",
                ]
                item = random.choice(shopping_items)
                amount = Decimal(str(random.randint(50, 200)))
                expense_entries.append(
                    Transaction(
                        user=self.user,
                        account=self.amex_card,
                        category=shopping_category,
                        description=item,
                        date=current_date,
                        amount=amount,
                        transaction_type="debit",
                        sync_source="manual",
                    )
                )

            # Travel (quarterly)
            if current_date.month in [3, 6, 9, 12] and current_date.day == 1:
                travel_expenses = [
                    ("United Airlines", Decimal("450.00")),
                    ("Marriott Hotel", Decimal("180.00")),
                    ("Hertz Car Rental", Decimal("85.50")),
                    ("Expedia Booking", Decimal("320.00")),
                ]
                travel_item, amount = travel_expenses[
                    (current_date.month // 3 - 1) % len(travel_expenses)
                ]
                expense_entries.append(
                    Transaction(
                        user=self.user,
                        account=self.amex_card,
                        category=travel_category,
                        description=travel_item,
                        date=current_date,
                        amount=amount,
                        transaction_type="debit",
                        sync_source="manual",
                    )
                )

            # Utilities (monthly on 1st)
            if current_date.day == 1:
                utilities = [
                    ("PG&E Electric", Decimal("85.00")),
                    ("Comcast Internet", Decimal("79.99")),
                    ("Water Bill", Decimal("45.50")),
                    ("Garbage Service", Decimal("35.00")),
                ]
                utility, amount = utilities[(current_date.month - 1) % len(utilities)]
                expense_entries.append(
                    Transaction(
                        user=self.user,
                        account=self.boa_card,
                        category=utilities_category,
                        description=utility,
                        date=current_date,
                        amount=amount,
                        transaction_type="debit",
                        sync_source="manual",
                    )
                )

            # Housing (monthly on 1st)
            if current_date.day == 1:
                expense_entries.append(
                    Transaction(
                        user=self.user,
                        account=self.boa_card,
                        category=housing_category,
                        description="Rent Payment",
                        date=current_date,
                        amount=Decimal("2200.00"),
                        transaction_type="debit",
                        sync_source="manual",
                    )
                )

            # Medical (every 3 months)
            if current_date.month % 3 == 0 and current_date.day == 10:
                medical_expenses = [
                    ("CVS Pharmacy", Decimal("25.00")),
                    ("Dental Checkup", Decimal("150.00")),
                    ("Eye Exam", Decimal("75.00")),
                    ("Prescription", Decimal("45.00")),
                ]
                medical_item, amount = medical_expenses[
                    (current_date.month // 3 - 1) % len(medical_expenses)
                ]
                expense_entries.append(
                    Transaction(
                        user=self.user,
                        account=self.boa_card,
                        category=medical_category,
                        description=medical_item,
                        date=current_date,
                        amount=amount,
                        transaction_type="debit",
                        sync_source="manual",
                    )
                )

            # Entertainment (monthly)
            if current_date.day == 20:
                entertainment_items = [
                    ("Netflix", Decimal("15.99")),
                    ("Movie Theater", Decimal("25.00")),
                    ("Concert Tickets", Decimal("85.00")),
                    ("Bowling", Decimal("35.00")),
                ]
                entertainment_item, amount = entertainment_items[
                    (current_date.month - 1) % len(entertainment_items)
                ]
                expense_entries.append(
                    Transaction(
                        user=self.user,
                        account=self.chase_card,
                        category=entertainment_category,
                        description=entertainment_item,
                        date=current_date,
                        amount=amount,
                        transaction_type="debit",
                        sync_source="manual",
                    )
                )

            # Subscriptions (monthly on 15th)
            if current_date.day == 15:
                subscriptions = [
                    ("Spotify Premium", Decimal("9.99")),
                    ("Adobe Creative Cloud", Decimal("52.99")),
                    ("Gym Membership", Decimal("45.00")),
                    ("Dropbox Pro", Decimal("11.99")),
                ]
                subscription, amount = subscriptions[
                    (current_date.month - 1) % len(subscriptions)
                ]
                expense_entries.append(
                    Transaction(
                        user=self.user,
                        account=self.amex_card,
                        category=subscriptions_category,
                        description=subscription,
                        date=current_date,
                        amount=amount,
                        transaction_type="debit",
                        sync_source="manual",
                    )
                )

            current_date += timedelta(days=1)

        # Bulk create all expense entries
        Transaction.objects.bulk_create(expense_entries, ignore_conflicts=True)

    def _create_budgets(self):
        """Create some basic budgets for the demo user using budget_v2."""
        categories = {
            c.slug: c for c in TransactionCategory.objects.filter(user=self.user)
        }
        today = self.today
        start_date = today.replace(day=1)

        # Calculate end of month
        if start_date.month == 12:
            end_date = start_date.replace(
                year=start_date.year + 1, month=1, day=1
            ) - timedelta(days=1)
        else:
            end_date = start_date.replace(
                month=start_date.month + 1, day=1
            ) - timedelta(days=1)

        # Create a monthly budget
        budget = Budget.objects.create(
            user=self.user,
            name=f"Monthly Budget - {start_date.strftime('%B %Y')}",
            period_type="monthly",
            start_date=start_date,
            end_date=end_date,
            is_active=True,
        )

        # Set budget categories
        budget_data = [
            ("groceries", 600),
            ("dining", 300),
            ("travel", 400),
            ("shopping", 250),
            ("utilities", 200),
        ]
        for cat_slug, amount in budget_data:
            category = categories.get(cat_slug)
            if category:
                BudgetCategory.objects.create(
                    budget=budget,
                    category=category,
                    allocated_amount=Decimal(str(amount)),
                )
