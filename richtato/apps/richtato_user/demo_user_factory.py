from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction

from richtato.apps.account.models import Account, AccountTransaction
from richtato.apps.expense.models import Expense
from richtato.apps.income.models import Income
from richtato.apps.richtato_user.models import CardAccount, Category, User


class DemoUserFactory:
    username = "demo"
    email = "demo@richtato.com"
    password = "demopassword123!"

    def __init__(self):
        self.user = None
        self.checking_account = None
        self.today = date.today()
        self.one_year_ago = self.today - timedelta(days=365)
        self.first_friday = self.get_previous_friday(self.today)

    @transaction.atomic
    def create_or_reset(self):
        self._delete_existing_user()
        self._create_user()
        self._create_credit_cards()
        self._create_accounts()
        self._create_income_transactions()
        self._create_expense_transactions()
        self._create_account_transactions()
        return self.user

    def get_previous_friday(self, d):
        return d - timedelta(days=(d.weekday() - 4) % 7)

    def _delete_existing_user(self):
        User.objects.filter(username=self.username).delete()

    def _create_user(self):
        self.user = User.objects.create_user(
            username=self.username, email=self.email, password=self.password
        )

    def _create_credit_cards(self):
        CardAccount.objects.bulk_create(
            [
                CardAccount(
                    user=self.user,
                    name="Bank of America Custom Cash",
                    bank="bank_of_america",
                ),
                CardAccount(
                    user=self.user,
                    name="American Express Platinum",
                    bank="american_express",
                ),
                CardAccount(
                    user=self.user, name="Chase Sapphire Preferred", bank="chase"
                ),
            ]
        )

    def _create_accounts(self):
        self.checking_account = Account.objects.create(
            user=self.user,
            type="checking",
            asset_entity_name="bank_of_america",
            name="Checking",
        )
        self.savings_account = Account.objects.create(
            user=self.user,
            type="savings",
            asset_entity_name="chase",
            name="Savings",
        )

    def _create_income_transactions(self):
        pay_dates = []
        current_friday = self.first_friday
        while current_friday >= self.one_year_ago:
            pay_dates.append(current_friday)
            current_friday -= timedelta(days=14)
        pay_dates.reverse()

        income_entries = []
        for pay_date in pay_dates:
            income_entries.extend(
                [
                    Income(
                        user=self.user,
                        account_name=self.checking_account,
                        description="Bi-weekly Salary",
                        date=pay_date,
                        amount=Decimal("3000.00"),
                    ),
                    Income(
                        user=self.user,
                        account_name=self.savings_account,
                        description="Bi-weekly Salary",
                        date=pay_date,
                        amount=Decimal("500.00"),
                    ),
                ]
            )
        Income.objects.bulk_create(income_entries, ignore_conflicts=True)

    def _create_expense_transactions(self):
        # Get card accounts for the demo user
        card_accounts = CardAccount.objects.filter(user=self.user)
        boa_card = card_accounts.filter(name="Bank of America Custom Cash").first()
        amex_card = card_accounts.filter(name="American Express Platinum").first()
        chase_card = card_accounts.filter(name="Chase Sapphire Preferred").first()

        # Get categories for the demo user
        categories = Category.objects.filter(user=self.user)
        travel_category = categories.filter(name="Travel").first()
        shopping_category = categories.filter(name="Shopping").first()
        groceries_category = categories.filter(name="Groceries").first()
        dining_category = categories.filter(name="Dining").first()
        utilities_category = categories.filter(name="Utilities").first()
        housing_category = categories.filter(name="Housing").first()
        medical_category = categories.filter(name="Medical").first()
        entertainment_category = categories.filter(name="Entertainment").first()
        subscriptions_category = categories.filter(name="Subscriptions").first()
        gas_category = categories.filter(name="Car").first()

        # Create a list of realistic expense transactions
        expense_entries = []

        # Generate dates for the past year
        current_date = self.one_year_ago
        while current_date <= self.today:
            # Groceries (weekly)
            if current_date.weekday() == 0:  # Monday
                expense_entries.append(
                    Expense(
                        user=self.user,
                        account_name=boa_card,
                        category=groceries_category,
                        description="Whole Foods Market",
                        date=current_date,
                        amount=Decimal("120.50"),
                    )
                )

            # Gas (every 2 weeks)
            if (
                current_date.weekday() == 2 and current_date.day % 14 < 7
            ):  # Wednesday every 2 weeks
                expense_entries.append(
                    Expense(
                        user=self.user,
                        account_name=boa_card,
                        category=gas_category,
                        description="Shell Gas Station",
                        date=current_date,
                        amount=Decimal("45.00"),
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
                    Expense(
                        user=self.user,
                        account_name=chase_card,
                        category=dining_category,
                        description=restaurant,
                        date=current_date,
                        amount=amount,
                    )
                )

            # Shopping (monthly)
            if current_date.day == 15:
                shopping_items = [
                    ("Amazon.com", Decimal("89.99")),
                    ("Target", Decimal("67.50")),
                    ("Walmart", Decimal("45.25")),
                    ("Best Buy", Decimal("199.99")),
                ]
                item, amount = shopping_items[
                    (current_date.month - 1) % len(shopping_items)
                ]
                expense_entries.append(
                    Expense(
                        user=self.user,
                        account_name=amex_card,
                        category=shopping_category,
                        description=item,
                        date=current_date,
                        amount=amount,
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
                    Expense(
                        user=self.user,
                        account_name=amex_card,
                        category=travel_category,
                        description=travel_item,
                        date=current_date,
                        amount=amount,
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
                    Expense(
                        user=self.user,
                        account_name=boa_card,
                        category=utilities_category,
                        description=utility,
                        date=current_date,
                        amount=amount,
                    )
                )

            # Housing (monthly on 1st)
            if current_date.day == 1:
                expense_entries.append(
                    Expense(
                        user=self.user,
                        account_name=boa_card,
                        category=housing_category,
                        description="Rent Payment",
                        date=current_date,
                        amount=Decimal("2200.00"),
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
                    Expense(
                        user=self.user,
                        account_name=boa_card,
                        category=medical_category,
                        description=medical_item,
                        date=current_date,
                        amount=amount,
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
                    Expense(
                        user=self.user,
                        account_name=chase_card,
                        category=entertainment_category,
                        description=entertainment_item,
                        date=current_date,
                        amount=amount,
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
                    Expense(
                        user=self.user,
                        account_name=amex_card,
                        category=subscriptions_category,
                        description=subscription,
                        date=current_date,
                        amount=amount,
                    )
                )

            current_date += timedelta(days=1)

        # Bulk create all expense entries
        Expense.objects.bulk_create(expense_entries, ignore_conflicts=True)

    def _create_account_transactions(self):
        """Create account transactions showing steadily rising balances"""
        # Starting balances
        checking_balance = Decimal("5000.00")  # Starting with $5,000
        savings_balance = Decimal("10000.00")  # Starting with $10,000

        # Generate transactions for the past year
        current_date = self.one_year_ago
        checking_transactions = []
        savings_transactions = []

        while current_date <= self.today:
            # Bi-weekly salary deposits (every 2 weeks on Friday)
            if (
                current_date.weekday() == 4
                and (current_date - self.one_year_ago).days % 14 < 7
            ):
                # Checking account gets $3,000 bi-weekly
                checking_balance += Decimal("3000.00")
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

                # Savings account gets $500 bi-weekly
                savings_balance += Decimal("500.00")
                savings_transactions.append(
                    AccountTransaction(
                        account=self.savings_account,
                        amount=savings_balance,
                        date=current_date,
                    )
                )

            # Monthly rent payment from checking (1st of each month)
            if current_date.day == 1:
                checking_balance -= Decimal("2200.00")
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

            # Monthly utility payments from checking (1st of each month)
            if current_date.day == 1:
                utilities_total = Decimal("245.49")  # Sum of all utilities
                checking_balance -= utilities_total
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

            # Grocery expenses from checking (weekly on Monday)
            if current_date.weekday() == 0:
                checking_balance -= Decimal("120.50")
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

            # Gas expenses from checking (every 2 weeks on Wednesday)
            if (
                current_date.weekday() == 2
                and (current_date - self.one_year_ago).days % 14 < 7
            ):
                checking_balance -= Decimal("45.00")
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

            # Medical expenses from checking (every 3 months on 10th)
            if current_date.month % 3 == 0 and current_date.day == 10:
                medical_amount = Decimal("73.75")  # Average medical expense
                checking_balance -= medical_amount
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

            # Monthly shopping expenses from checking (15th of each month)
            if current_date.day == 15:
                shopping_amount = Decimal("100.68")  # Average shopping expense
                checking_balance -= shopping_amount
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

            # Monthly entertainment expenses from checking (20th of each month)
            if current_date.day == 20:
                entertainment_amount = Decimal("40.25")  # Average entertainment expense
                checking_balance -= entertainment_amount
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

            # Monthly subscription expenses from checking (15th of each month)
            if current_date.day == 15:
                subscription_amount = Decimal("30.00")  # Average subscription expense
                checking_balance -= subscription_amount
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

            # Weekend dining expenses from checking (randomly 2-3 times per week)
            if current_date.weekday() in [4, 5, 6] and current_date.day % 7 < 3:
                dining_amount = Decimal("14.56")  # Average dining expense
                checking_balance -= dining_amount
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

            # Quarterly travel expenses from checking (1st of March, June, September, December)
            if current_date.month in [3, 6, 9, 12] and current_date.day == 1:
                travel_amount = Decimal("259.13")  # Average travel expense
                checking_balance -= travel_amount
                checking_transactions.append(
                    AccountTransaction(
                        account=self.checking_account,
                        amount=checking_balance,
                        date=current_date,
                    )
                )

            current_date += timedelta(days=1)

        # Bulk create all account transactions
        all_transactions = checking_transactions + savings_transactions
        AccountTransaction.objects.bulk_create(all_transactions, ignore_conflicts=True)
