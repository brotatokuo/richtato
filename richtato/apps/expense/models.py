from apps.richtato_user.models import CardAccount, Category, User
from django.db import models
from utilities.db_model import DB
from utilities.tools import convert_currency_to_float


# Create your models here.
class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transaction")
    account_name = models.ForeignKey(
        CardAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="transactions"
    )
    description = models.CharField(max_length=100)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description}"

    @classmethod
    def existing_years_for_user(cls, user):
        # Query all expenses for the given user where the date is not null
        expenses = cls.objects.filter(user=user, date__isnull=False)

        years = {expense.date.year for expense in expenses}

        # Return the dictionary where keys are years and values are lists of months
        return sorted(years)


class ExpenseDB(DB):
    def __init__(self, user: User):
        self.user = user

    def add(
        self,
        account: str,
        description: str,
        category: str,
        date: str,
        amount: str | float,
    ):
        amount = convert_currency_to_float(amount)
        category_obj = Category.objects.get(user=self.user, name=category)
        account_name = CardAccount.objects.get(user=self.user, name=account)
        transaction = Expense(
            user=self.user,
            account_name=account_name,
            description=description,
            category=category_obj,
            date=date,
            amount=amount,
        )
        transaction.save()

    def delete(self, transaction_id: int) -> None:
        try:
            Expense.objects.get(id=transaction_id).delete()
        except Expense.DoesNotExist:
            raise ValueError(f"Transaction with ID '{transaction_id}' does not exist.")

    def get_category(self, category_name: str, transaction_id: int) -> Category:
        if category_name:
            try:
                return Category.objects.get(user=self.user, name=category_name)
            except Category.DoesNotExist:
                raise ValueError(
                    f"Category '{category_name}' does not exist for the user."
                )
        else:
            return Expense.objects.get(id=transaction_id).category

    def get_account(self, account_name: str) -> CardAccount:
        try:
            return CardAccount.objects.get(user=self.user, name=account_name)
        except CardAccount.DoesNotExist:
            raise ValueError(f"Account '{account_name}' does not exist for the user.")

    def update(
        self,
        transaction_id: int,
        date: str,
        description: str,
        amount: float | str,
        category: str,
        account: str,
    ):
        category_obj = ExpenseDB(self.user).get_category(category, transaction_id)
        account_obj = ExpenseDB(self.user).get_account(account)
        Expense.objects.update_or_create(
            user=self.user,
            id=transaction_id,
            defaults={
                "date": date,
                "description": description,
                "amount": convert_currency_to_float(amount),
                "category": category_obj,
                "account_name": account_obj,
            },
        )
