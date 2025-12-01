"""Teller connection serializers."""

from rest_framework import serializers

from .models import TellerConnection


class TellerConnectionSerializer(serializers.ModelSerializer):
    """Serializer for Teller connections."""

    class Meta:
        model = TellerConnection
        fields = [
            "id",
            "teller_account_id",
            "enrollment_id",
            "institution_name",
            "account_name",
            "account_type",
            "status",
            "last_sync",
            "last_sync_error",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "last_sync",
            "last_sync_error",
            "created_at",
        ]


class TellerConnectionCreateSerializer(serializers.Serializer):
    """Serializer for creating new Teller connections."""

    access_token = serializers.CharField(required=True)
    enrollment_id = serializers.CharField(required=False, allow_blank=True)
    teller_account_id = serializers.CharField(required=True)
    institution_name = serializers.CharField(required=True)
    account_name = serializers.CharField(required=True)
    account_type = serializers.CharField(required=False, allow_blank=True)


class TellerSyncResponseSerializer(serializers.Serializer):
    """Serializer for sync operation responses."""

    success = serializers.BooleanField()
    accounts_synced = serializers.IntegerField(default=0)
    transactions_synced = serializers.IntegerField(default=0)
    errors = serializers.ListField(child=serializers.CharField(), default=list)
    message = serializers.CharField()
