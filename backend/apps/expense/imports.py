import pandas as pd
from django.db import models
from loguru import logger

from apps.expense.serializers import ExpenseSerializer
from apps.richtato_user.models import CardAccount, Category


class ExpenseManager(models.Manager):
    @classmethod
    def import_from_dataframe(cls, df: pd.DataFrame, user):
        for _, row in df.iterrows():
            try:
                account = CardAccount.objects.get(name=row["Card"], user=user)

                try:
                    category = Category.objects.get(name=row["Category"], user=user)
                except Category.DoesNotExist:
                    category, _ = Category.objects.get_or_create(
                        name="Unknown", user=user
                    )

                data = {
                    "user": user.id,
                    "amount": row["Amount"],
                    "date": row["Date"],
                    "description": row["Description"],
                    "account_name": account.id,
                    "category": category.id,
                }

                serializer = ExpenseSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    logger.error(f"Invalid row: {serializer.errors}")
            except Exception as e:
                logger.error(f"Error processing row: {e}")
