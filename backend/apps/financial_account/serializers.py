"""Serializers for financial accounts."""

from decimal import Decimal

from rest_framework import serializers

from apps.financial_account.institutions.registry import (
    ACCOUNT_TYPE_LABELS,
    agent_flow_for_account,
    is_valid_account_type,
)

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
    opening_balance = serializers.SerializerMethodField()
    opening_balance_date = serializers.SerializerMethodField()

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
            "agent_cadence",
            "agent_sync_hour",
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
            "opening_balance",
            "opening_balance_date",
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

    def get_opening_balance(self, obj):
        from apps.financial_account.services.account_service import AccountService

        balance, _balance_date = AccountService().get_opening_balance(obj)
        if balance is None:
            return None
        return str(balance.quantize(Decimal("0.01")))

    def get_opening_balance_date(self, obj):
        from apps.financial_account.services.account_service import AccountService

        _balance, balance_date = AccountService().get_opening_balance(obj)
        if balance_date is None:
            return None
        return balance_date.isoformat()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class FinancialAccountCreateSerializer(serializers.Serializer):
    """Serializer for creating manual financial accounts."""

    name = serializers.CharField(max_length=255)
    account_type = serializers.ChoiceField(choices=list(ACCOUNT_TYPE_LABELS.keys()))
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

    def validate(self, attrs):
        institution_slug = attrs.get("institution_slug") or "other"
        account_type = attrs["account_type"]
        if not is_valid_account_type(institution_slug, account_type):
            raise serializers.ValidationError(
                {
                    "account_type": (
                        f"Account type '{account_type}' is not supported for institution '{institution_slug}'."
                    )
                }
            )
        return attrs


class FinancialAccountUpdateSerializer(serializers.Serializer):
    """Serializer for updating financial accounts."""

    name = serializers.CharField(max_length=255, required=False)
    account_type = serializers.ChoiceField(choices=list(ACCOUNT_TYPE_LABELS.keys()), required=False)
    institution_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    institution_slug = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Slug of preset institution (e.g., 'chase', 'guideline')",
    )
    account_number_last4 = serializers.CharField(max_length=4, required=False, allow_blank=True)
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    is_active = serializers.BooleanField(required=False)
    image_key = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    shared_with_household = serializers.BooleanField(required=False)
    storage_uri = serializers.CharField(max_length=512, required=False, allow_blank=True)
    agent_activity_url = serializers.URLField(required=False, allow_blank=True, max_length=2048)
    opening_balance = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        allow_null=True,
    )
    opening_balance_date = serializers.DateField(required=False, allow_null=True)
    sync_mode = serializers.ChoiceField(
        choices=["auto", "upload", "manual"],
        required=False,
    )
    agent_cadence = serializers.ChoiceField(
        choices=["manual", "daily", "weekly", "monthly"],
        required=False,
    )
    agent_sync_hour = serializers.IntegerField(min_value=0, max_value=23, required=False)

    def validate(self, attrs):
        account = self.context.get("account")

        institution_slug = attrs.get("institution_slug")
        if institution_slug is None and account and account.institution:
            institution_slug = account.institution.slug
        elif institution_slug is None:
            institution_slug = "other"

        account_type = attrs.get("account_type")
        if account_type is None and account:
            account_type = account.account_type

        if attrs.get("institution_slug") is not None or attrs.get("account_type") is not None:
            if account_type and not is_valid_account_type(institution_slug, account_type):
                raise serializers.ValidationError(
                    {
                        "account_type": (
                            f"Account type '{account_type}' is not supported for institution '{institution_slug}'."
                        )
                    }
                )

        sync_mode = attrs.get("sync_mode")
        if sync_mode == "auto":
            if agent_flow_for_account(institution_slug, account_type or "") is None:
                raise serializers.ValidationError(
                    {
                        "sync_mode": (
                            "Auto sync is not available for this institution and account type. "
                            "Use upload or manual instead."
                        )
                    }
                )

        return attrs
