from apps.account.models import Account
from apps.richtato_user.models import User
from django.db import models
from loguru import logger
from utilities.tools import convert_currency_to_float


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="earning")
    account_name = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="earning"
    )
    description = models.CharField(max_length=100)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} [{self.account_name}] (${self.amount}) {self.description}"


class IncomeDB:
    def __init__(self, user: User):
        self.user = user

    def add(self, account: str, description: str, date: str, amount: str) -> None:
        logger.info("Adding income transaction")
        logger.debug(f"Account: {account}")
        logger.debug(f"Description: {description}")
        logger.debug(f"Date: {date}")
        logger.debug(f"Amount: {amount}")
        account_name = Account.objects.get(user=self.user, name=account)
        transaction = Income(
            user=self.user,
            account_name=account_name,
            description=description,
            date=date,
            amount=convert_currency_to_float(amount),
        )
        transaction.save()

    def delete(self, transaction_id: int) -> None:
        try:
            Income.objects.get(id=transaction_id).delete()
        except Income.DoesNotExist:
            pass

    def update(
        self,
        transaction_id: int,
        date: str,
        description: str,
        amount: str,
    ) -> None:
        try:
            Income.objects.update_or_create(
                user=self.user,
                id=transaction_id,
                defaults={
                    "date": date,
                    "description": description,
                    "amount": convert_currency_to_float(amount),
                },
            )
        except Income.DoesNotExist:
            pass
