from rest_framework import serializers

from richtato.apps.richtato_user.models import CardAccount, Category

from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    Account = serializers.PrimaryKeyRelatedField(
        queryset=CardAccount.objects.all(), source="account_name"
    )
    Category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category"
    )

    class Meta:
        model = Expense
        fields = [
            "id",
            "amount",
            "date",
            "description",
            "Category",
            "Account",
        ]
        read_only_fields = ["id"]
