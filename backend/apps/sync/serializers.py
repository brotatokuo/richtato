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
    """Serializer for creating Teller sync connections."""

    account_id = serializers.IntegerField()
    access_token = serializers.CharField()
    external_account_id = serializers.CharField()
    institution_name = serializers.CharField()
    external_enrollment_id = serializers.CharField(required=False, allow_blank=True)
