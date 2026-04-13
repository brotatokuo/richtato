"""Serializers for budgets."""

from rest_framework import serializers

from .models import Budget, BudgetCategory


class BudgetCategorySerializer(serializers.ModelSerializer):
    """Serializer for budget categories."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    category_full_path = serializers.CharField(source="category.full_path", read_only=True)
    total_available = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = BudgetCategory
        fields = [
            "id",
            "category",
            "category_name",
            "category_full_path",
            "allocated_amount",
            "rollover_enabled",
            "rollover_amount",
            "total_available",
        ]
        read_only_fields = ["id"]


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for budgets."""

    budget_categories = BudgetCategorySerializer(many=True, read_only=True)
    period_type_display = serializers.CharField(source="get_period_type_display", read_only=True)

    class Meta:
        model = Budget
        fields = [
            "id",
            "name",
            "period_type",
            "period_type_display",
            "start_date",
            "end_date",
            "is_active",
            "budget_categories",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BudgetCreateSerializer(serializers.Serializer):
    """Serializer for creating budgets."""

    name = serializers.CharField(max_length=255)
    period_type = serializers.ChoiceField(choices=["monthly", "yearly", "custom"])
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    categories = serializers.ListField(child=serializers.DictField(), required=False, allow_empty=True)


class BudgetCategoryCreateSerializer(serializers.Serializer):
    """Serializer for adding categories to budgets."""

    category_id = serializers.IntegerField()
    allocated_amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0)
    rollover_enabled = serializers.BooleanField(default=False)
