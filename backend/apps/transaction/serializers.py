"""Serializers for transactions."""

from rest_framework import serializers

from .models import KeywordRule, Merchant, Transaction, TransactionCategory


class TransactionCategorySerializer(serializers.ModelSerializer):
    """Serializer for transaction categories."""

    parent_name = serializers.CharField(source="parent.name", read_only=True)
    full_path = serializers.CharField(read_only=True)

    class Meta:
        model = TransactionCategory
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "parent_name",
            "full_path",
            "icon",
            "color",
            "is_income",
            "is_expense",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MerchantSerializer(serializers.ModelSerializer):
    """Serializer for merchants."""

    class Meta:
        model = Merchant
        fields = ["id", "name", "slug", "category_hint", "logo_url"]
        read_only_fields = ["id"]


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions."""

    account_name = serializers.CharField(source="account.name", read_only=True)
    category_name = serializers.CharField(read_only=True)
    merchant_name = serializers.CharField(source="merchant.name", read_only=True)
    signed_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )
    categorization_status_display = serializers.CharField(
        source="get_categorization_status_display", read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "account_name",
            "date",
            "amount",
            "signed_amount",
            "description",
            "transaction_type",
            "transaction_type_display",
            "category",
            "category_name",
            "merchant",
            "merchant_name",
            "status",
            "is_recurring",
            "sync_source",
            "categorization_status",
            "categorization_status_display",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "sync_source",
            "categorization_status",
            "created_at",
            "updated_at",
        ]


class TransactionCreateSerializer(serializers.Serializer):
    """Serializer for creating manual transactions."""

    account_id = serializers.IntegerField()
    date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0)
    description = serializers.CharField(max_length=500)
    transaction_type = serializers.ChoiceField(
        choices=["debit", "credit"], default="debit"
    )
    category_id = serializers.IntegerField(required=False, allow_null=True)
    merchant_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    status = serializers.ChoiceField(
        choices=["pending", "posted", "reconciled"], default="posted"
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2000
    )


class TransactionUpdateSerializer(serializers.Serializer):
    """Serializer for updating transactions."""

    date = serializers.DateField(required=False)
    amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, min_value=0, required=False
    )
    description = serializers.CharField(max_length=500, required=False)
    transaction_type = serializers.ChoiceField(
        choices=["debit", "credit"], required=False
    )
    category_id = serializers.IntegerField(required=False, allow_null=True)
    merchant_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    status = serializers.ChoiceField(
        choices=["pending", "posted", "reconciled"], required=False
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2000
    )


class TransactionCategorizeSerializer(serializers.Serializer):
    """Serializer for categorizing transactions."""

    category_id = serializers.IntegerField()


class CategoryCreateSerializer(serializers.Serializer):
    """Serializer for creating custom categories."""

    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=255)
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    icon = serializers.CharField(max_length=50, required=False, allow_blank=True)
    color = serializers.CharField(max_length=7, required=False, allow_blank=True)
    is_income = serializers.BooleanField(default=False)
    is_expense = serializers.BooleanField(default=True)


class KeywordRuleSerializer(serializers.ModelSerializer):
    """Serializer for keyword rules."""

    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = KeywordRule
        fields = ["id", "keyword", "category", "category_name", "created_at"]
        read_only_fields = ["id", "created_at", "category_name"]
