from rest_framework import serializers

from .models import Account, AccountTransaction


class AccountTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountTransaction
        fields = ["id", "account", "amount", "date"]


class AccountSerializer(serializers.ModelSerializer):
    history = AccountTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Account
        fields = [
            "id",
            "user",
            "type",
            "asset_entity_name",
            "name",
            "latest_balance",
            "latest_balance_date",
            "history",
        ]
        read_only_fields = ["id", "latest_balance", "latest_balance_date", "user"]
