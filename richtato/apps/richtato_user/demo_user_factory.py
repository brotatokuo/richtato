from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction

from richtato.apps.account.models import Account
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
        Account.objects.create(
            user=self.user,
            type="savings",
            asset_entity_name="bank_of_america",
            name="Savings",
        )

    def _create_income_transactions(self):
        pay_dates = []
        current_friday = self.first_friday
        while current_friday >= self.one_year_ago:
            pay_dates.append(current_friday)
            current_friday -= timedelta(days=14)
        pay_dates.reverse()

        income_entries = [
            Income(
                user=self.user,
                account_name=self.checking_account,
                description="Bi-weekly Salary",
                date=pay_date,
                amount=Decimal("3000.00"),
            )
            for pay_date in pay_dates
        ]
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
