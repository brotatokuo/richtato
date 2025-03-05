from apps.richtato_user.models import CardAccount, Category, User
from django.db import models


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


class ExpenseTransactions:
    def __init__(self, user: User):
        self.user = user

    @staticmethod
    def add_entry(
        user: User,
        account: str,
        description: str,
        category: str,
        date: str,
        amount: str,
    ):
        category_obj = Category.objects.get(user=user, name=category)
        account_name = CardAccount.objects.get(user=user, name=account)
        transaction = Expense(
            user=user,
            account_name=account_name,
            description=description,
            category=category_obj,
            date=date,
            amount=amount,
        )
        transaction.save()

    @staticmethod
    def delete_expense(transaction_id: int) -> None:
        try:
            Expense.objects.get(id=transaction_id).delete()
        except Expense.DoesNotExist:
            raise ValueError(f"Transaction with ID '{transaction_id}' does not exist.")

    @staticmethod
    def get_category(user: User, category_name: str, transaction_id: int) -> Category:
        if category_name:
            try:
                return Category.objects.get(user=user, name=category_name)
            except Category.DoesNotExist:
                raise ValueError(
                    f"Category '{category_name}' does not exist for the user."
                )
        else:
            return Expense.objects.get(id=transaction_id).category

    @staticmethod
    def get_account(user: User, account_name: str) -> CardAccount:
        try:
            return CardAccount.objects.get(user=user, name=account_name)
        except CardAccount.DoesNotExist:
            raise ValueError(f"Account '{account_name}' does not exist for the user.")

    @staticmethod
    def update(
        user: User,
        transaction_id: int,
        date: str,
        description: str,
        amount: float,
        category: str,
        account: str,
    ):
        category_obj = ExpenseTransactions.get_category(user, category, transaction_id)
        account_obj = ExpenseTransactions.get_account(user, account)
        Expense.objects.update_or_create(
            user=user,
            id=transaction_id,
            defaults={
                "date": date,
                "description": description,
                "amount": amount,
                "category": category_obj,
                "account_name": account_obj,
            },
        )
