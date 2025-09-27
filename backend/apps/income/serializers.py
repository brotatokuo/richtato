from rest_framework import serializers

from apps.account.models import Account

from .models import Income


class IncomeSerializer(serializers.ModelSerializer):
    Account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(), source="account_name"
    )

    class Meta:
        model = Income
        fields = ["id", "Account", "description", "date", "amount"]
        read_only_fields = ["id"]
