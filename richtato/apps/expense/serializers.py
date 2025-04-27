from rest_framework import serializers

from richtato.apps.expense.models import Expense
from richtato.apps.richtato_user.models import CardAccount, Category, User


class ExpenseSerializer(serializers.ModelSerializer):
    account_name = serializers.PrimaryKeyRelatedField(
        queryset=CardAccount.objects.all()
    )
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Expense
        fields = [
            "id",
            "amount",
            "date",
            "description",
            "user",
            "category",
            "account_name",
        ]
        read_only_fields = ["id"]
