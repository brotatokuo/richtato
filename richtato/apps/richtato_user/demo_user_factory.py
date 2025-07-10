from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction

from richtato.apps.account.models import Account
from richtato.apps.income.models import Income
from richtato.apps.richtato_user.models import CardAccount, User


class DemoUserFactory:
    username = "demo"
    password = "demopassword123!"

    def __init__(self):
        self.user = None
        self.checking_account = None

    @transaction.atomic
    def create_or_reset(self):
        self._delete_existing_user()
        self._create_user()
        self._create_credit_cards()
        self._create_accounts()
        self._create_income_transactions()
        # self._create_expense_transactions_from_csv()  # (optional)
        return self.user

    def _delete_existing_user(self):
        User.objects.filter(username=self.username).delete()

    def _create_user(self):
        self.user = User.objects.create_user(
            username=self.username, password=self.password
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
        today = date.today()
        one_year_ago = today - timedelta(days=365)

        def get_previous_friday(d):
            return d - timedelta(days=(d.weekday() - 4) % 7)

        first_friday = get_previous_friday(today)

        pay_dates = []
        while first_friday >= one_year_ago:
            pay_dates.append(first_friday)
            first_friday -= timedelta(days=14)
        pay_dates.reverse()

        income_entries = [
            Income(
                user=self.user,
                account_name=self.checking_account,
                description="Bi-weekly Salary",
                date=pay_date,
                amount=Decimal("5000.00"),
            )
            for pay_date in pay_dates
        ]
        Income.objects.bulk_create(income_entries, ignore_conflicts=True)
