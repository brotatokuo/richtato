"""Serializers for sync connections and jobs."""

from rest_framework import serializers

from .models import SyncConnection, SyncJob


class SyncConnectionSerializer(serializers.ModelSerializer):
    """Serializer for sync connections."""

    account_name = serializers.CharField(source="account.name", read_only=True)
    provider_display = serializers.CharField(
        source="get_provider_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SyncConnection
        fields = [
            "id",
            "account",
            "account_name",
            "provider",
            "provider_display",
            "institution_name",
            "external_account_id",
            "status",
            "status_display",
            "last_sync",
            "sync_frequency",
            "initial_backfill_complete",
            "oldest_transaction_date",
            "last_sync_error",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "last_sync",
            "initial_backfill_complete",
            "oldest_transaction_date",
            "last_sync_error",
            "created_at",
        ]


class SyncJobSerializer(serializers.ModelSerializer):
    """Serializer for sync jobs."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = SyncJob
        fields = [
            "id",
            "connection",
            "status",
            "status_display",
            "is_full_sync",
            "started_at",
            "completed_at",
            "duration_seconds",
            "transactions_synced",
            "transactions_skipped",
            "batches_processed",
            "errors",
        ]
        read_only_fields = ["id"]

    def get_duration_seconds(self, obj):
        """Get duration in seconds."""
        if obj.duration:
            return obj.duration.total_seconds()
        return None


class SyncConnectionCreateSerializer(serializers.Serializer):
    """Serializer for creating sync connections (Plaid).

    Supports two modes:
    1. Enrollment mode: Provide access_token, institution_name, and external_enrollment_id.
       Backend will fetch accounts from the provider and create connections for each.
    2. Direct mode: Provide all fields including external_account_id for a single account.
    """

    # Provider: 'plaid'
    provider = serializers.ChoiceField(
        choices=["plaid"], required=False, default="plaid"
    )
    # Either provide account_id OR account_name + account_type to auto-create
    account_id = serializers.IntegerField(required=False)
    account_name = serializers.CharField(required=False, allow_blank=True)
    account_type = serializers.CharField(required=False, default="checking")
    access_token = serializers.CharField()
    # Optional - if not provided or starts with 'enr_', backend fetches accounts from provider
    external_account_id = serializers.CharField(required=False, allow_blank=True)
    institution_name = serializers.CharField()
    external_enrollment_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Validate the request data."""
        external_account_id = data.get("external_account_id", "")
        external_enrollment_id = data.get("external_enrollment_id", "")

        # If external_account_id is provided and NOT an enrollment ID,
        # we need account info for direct creation
        is_enrollment_mode = (
            not external_account_id
            or external_account_id.startswith("enr_")
            or external_enrollment_id
        )

        if not is_enrollment_mode:
            # Direct mode - need account info
            if not data.get("account_id") and not data.get("account_name"):
                raise serializers.ValidationError(
                    "Either account_id or account_name must be provided for direct account creation"
                )

        return data
