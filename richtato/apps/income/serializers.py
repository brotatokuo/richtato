from rest_framework import serializers

from .models import Income


class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = [
            "id",
            "user",
            "account_name",
            "description",
            "date",
            "amount",
        ]
