from apps.expense.models import Expense
from apps.richtato_user.models import User
from apps.category.models import Category
from apps.card.models import CardAccount
from rest_framework import serializers


class ExpenseSerializer(serializers.ModelSerializer):
    account_name = serializers.PrimaryKeyRelatedField(
        queryset=CardAccount.objects.all()
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), allow_null=True, required=False
    )
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Expense
        fields = [
            "id",
            "user",
            "account_name",
            "category",
            "description",
            "date",
            "amount",
            "details",
        ]
        read_only_fields = ["id"]
