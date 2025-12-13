"""Serializers for financial accounts."""

from rest_framework import serializers

from .models import AccountBalanceHistory, FinancialAccount, FinancialInstitution


class FinancialInstitutionSerializer(serializers.ModelSerializer):
    """Serializer for financial institutions."""

    class Meta:
        model = FinancialInstitution
        fields = ["id", "name", "slug", "logo_url", "support_url"]
        read_only_fields = ["id"]


class AccountBalanceHistorySerializer(serializers.ModelSerializer):
    """Serializer for account balance history."""

    class Meta:
        model = AccountBalanceHistory
        fields = ["id", "date", "balance", "created_at"]
        read_only_fields = ["id", "created_at"]


class FinancialAccountSerializer(serializers.ModelSerializer):
    """Serializer for financial accounts."""

    institution_name = serializers.CharField(source="institution.name", read_only=True)
    account_type_display = serializers.CharField(
        source="get_account_type_display", read_only=True
    )
    # Backward compatibility aliases
    type = serializers.CharField(source="account_type", read_only=True)
    type_display = serializers.CharField(
        source="get_account_type_display", read_only=True
    )
    entity = serializers.SerializerMethodField()
    entity_display = serializers.CharField(source="institution.name", read_only=True)
    date = serializers.DateTimeField(source="updated_at", read_only=True)

    # Sync connection fields
    has_connection = serializers.SerializerMethodField()
    connection_id = serializers.SerializerMethodField()
    connection_status = serializers.SerializerMethodField()
    last_sync = serializers.SerializerMethodField()

    class Meta:
        model = FinancialAccount
        fields = [
            "id",
            "name",
            "institution",
            "institution_name",
            "account_number_last4",
            "account_type",
            "account_type_display",
            "balance",
            "currency",
            "is_active",
            "sync_source",
            "image_key",
            "created_at",
            "updated_at",
            # Backward compatibility
            "type",
            "type_display",
            "entity",
            "entity_display",
            "date",
            # Sync connection fields
            "has_connection",
            "connection_id",
            "connection_status",
            "last_sync",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "sync_source"]

    def _get_active_connection(self, obj):
        """Get the active sync connection for this account."""
        # Use prefetched data if available, otherwise query
        if (
            hasattr(obj, "_prefetched_objects_cache")
            and "sync_connections" in obj._prefetched_objects_cache
        ):
            connections = obj._prefetched_objects_cache["sync_connections"]
            for conn in connections:
                if conn.status in ("active", "error"):
                    return conn
            return None
        # Fallback to query
        return obj.sync_connections.filter(status__in=["active", "error"]).first()

    def get_has_connection(self, obj):
        """Check if account has an active sync connection."""
        return self._get_active_connection(obj) is not None

    def get_connection_id(self, obj):
        """Get the sync connection ID if exists."""
        conn = self._get_active_connection(obj)
        return conn.id if conn else None

    def get_connection_status(self, obj):
        """Get the sync connection status."""
        conn = self._get_active_connection(obj)
        return conn.status if conn else None

    def get_last_sync(self, obj):
        """Get the last sync timestamp."""
        conn = self._get_active_connection(obj)
        if conn and conn.last_sync:
            return conn.last_sync.isoformat()
        return None

    def get_entity(self, obj):
        """Return institution slug or name for backward compatibility."""
        if obj.institution:
            return obj.institution.slug or obj.institution.name.lower().replace(
                " ", "_"
            )
        return "manual"

    def to_representation(self, instance):
        """Flip balance sign for credit accounts at serialization time."""
        data = super().to_representation(instance)
        account_type = (instance.account_type or "").lower()
        if account_type in ["credit", "credit_card"]:
            # Ensure balance is represented as negative for liabilities
            balance = data.get("balance")
            try:
                data["balance"] = -1 * float(balance)
            except Exception:
                pass
        return data


class FinancialAccountCreateSerializer(serializers.Serializer):
    """Serializer for creating manual financial accounts."""

    name = serializers.CharField(max_length=255)
    account_type = serializers.ChoiceField(
        choices=["checking", "savings", "credit_card"]
    )
    institution_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    institution_slug = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Slug of preset institution (e.g., 'chase', 'bank_of_america')",
    )
    account_number_last4 = serializers.CharField(
        max_length=4, required=False, allow_blank=True
    )
    initial_balance = serializers.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    currency = serializers.CharField(max_length=3, default="USD")


class FinancialAccountUpdateSerializer(serializers.Serializer):
    """Serializer for updating financial accounts."""

    name = serializers.CharField(max_length=255, required=False)
    institution_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    account_number_last4 = serializers.CharField(
        max_length=4, required=False, allow_blank=True
    )
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    is_active = serializers.BooleanField(required=False)
    image_key = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True
    )
