"""Serializers for transactions."""

from rest_framework import serializers

from .models import CategoryKeyword, Transaction, TransactionCategory


class CategoryKeywordSerializer(serializers.ModelSerializer):
    """Serializer for category keywords."""

    class Meta:
        model = CategoryKeyword
        fields = ["id", "user", "keyword", "match_count", "created_at"]
        read_only_fields = ["id", "user", "match_count", "created_at"]


class TransactionCategorySerializer(serializers.ModelSerializer):
    """Serializer for transaction categories."""

    parent_name = serializers.CharField(source="parent.name", read_only=True)
    full_path = serializers.CharField(read_only=True)
    keywords = CategoryKeywordSerializer(many=True, read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    expense_priority_display = serializers.CharField(
        source="get_expense_priority_display", read_only=True
    )
    is_essential = serializers.SerializerMethodField()

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
            "type",
            "type_display",
            "expense_priority",
            "expense_priority_display",
            "is_essential",
            "keywords",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_is_essential(self, obj):
        """Return True if category is essential, False otherwise."""
        return obj.expense_priority == "essential"


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions."""

    account_name = serializers.CharField(source="account.name", read_only=True)
    category_name = serializers.CharField(read_only=True)
    category_type = serializers.SerializerMethodField()
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
            "category_type",
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

    def get_category_type(self, obj):
        """Return category type or 'uncategorized'."""
        if obj.category:
            return obj.category.type
        return "uncategorized"


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
    type = serializers.ChoiceField(
        choices=["income", "expense", "transfer"], default="expense"
    )
    expense_priority = serializers.ChoiceField(
        choices=["essential", "non_essential"],
        required=False,
        allow_null=True,
        help_text="Only applies to expense categories",
    )
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        allow_empty=True,
        help_text="List of keywords for this category",
    )


class CategoryUpdateSerializer(serializers.Serializer):
    """Serializer for updating categories."""

    name = serializers.CharField(max_length=255, required=False)
    icon = serializers.CharField(max_length=50, required=False, allow_blank=True)
    color = serializers.CharField(max_length=7, required=False, allow_blank=True)
    expense_priority = serializers.ChoiceField(
        choices=["essential", "non_essential"],
        required=False,
        allow_null=True,
        help_text="Only applies to expense categories",
    )


class CategoryKeywordCreateSerializer(serializers.Serializer):
    """Serializer for adding keywords to a category."""

    keyword = serializers.CharField(max_length=200)
