from rest_framework import serializers

from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            "id",
            "user",
            "amount",
            "date",
            "description",
            "category",  # Not working
            "account_name",
        ]
        read_only_fields = ["id", "user"]
