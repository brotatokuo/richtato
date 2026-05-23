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
    account_type_display = serializers.CharField(source="get_account_type_display", read_only=True)
    # Backward compatibility aliases
    type = serializers.CharField(source="account_type", read_only=True)
    type_display = serializers.CharField(source="get_account_type_display", read_only=True)
    entity = serializers.SerializerMethodField()
    entity_display = serializers.CharField(source="institution.name", read_only=True)
    date = serializers.SerializerMethodField()
    resolved_storage_uri = serializers.SerializerMethodField()

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
            "sync_mode",
            "storage_uri",
            "resolved_storage_uri",
            "image_key",
            "shared_with_household",
            "created_at",
            "updated_at",
            # Backward compatibility
            "type",
            "type_display",
            "entity",
            "entity_display",
            "date",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "sync_source", "resolved_storage_uri"]

    def get_resolved_storage_uri(self, obj):
        """Return the effective storage URI (override or convention default)."""
        return obj.resolved_storage_uri()

    def get_date(self, obj):
        """Return the most recent balance history date, falling back to updated_at."""
        latest = obj.balance_history.order_by("-date").values_list("date", flat=True).first()
        if latest:
            return latest.isoformat()
        return obj.updated_at.isoformat() if obj.updated_at else None

    def get_entity(self, obj):
        """Return institution slug or name for backward compatibility."""
        if obj.institution:
            return obj.institution.slug or obj.institution.name.lower().replace(" ", "_")
        return "manual"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class FinancialAccountCreateSerializer(serializers.Serializer):
    """Serializer for creating manual financial accounts."""

    name = serializers.CharField(max_length=255)
    account_type = serializers.ChoiceField(choices=["checking", "savings", "credit_card"])
    institution_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    institution_slug = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Slug of preset institution (e.g., 'chase', 'bank_of_america')",
    )
    account_number_last4 = serializers.CharField(max_length=4, required=False, allow_blank=True)
    initial_balance = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = serializers.CharField(max_length=3, default="USD")


class FinancialAccountUpdateSerializer(serializers.Serializer):
    """Serializer for updating financial accounts."""

    name = serializers.CharField(max_length=255, required=False)
    institution_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    account_number_last4 = serializers.CharField(max_length=4, required=False, allow_blank=True)
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    is_active = serializers.BooleanField(required=False)
    image_key = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    shared_with_household = serializers.BooleanField(required=False)
    storage_uri = serializers.CharField(max_length=512, required=False, allow_blank=True)
