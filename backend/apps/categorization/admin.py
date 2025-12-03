"""Admin configuration for categorization."""

from django.contrib import admin

from .models import (
    CategorizationHistory,
    CategorizationQueue,
    CategorizationRule,
    UserCategorizationPreference,
)


@admin.register(CategorizationRule)
class CategorizationRuleAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "condition_type",
        "condition_value",
        "category",
        "priority",
        "is_active",
        "created_at",
    )
    list_filter = ("condition_type", "is_active", "created_at")
    search_fields = ("user__username", "condition_value", "category__name")
    list_select_related = ("user", "category")


@admin.register(CategorizationHistory)
class CategorizationHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "transaction",
        "category",
        "method",
        "confidence_score",
        "created_at",
    )
    list_filter = ("method", "created_at")
    search_fields = ("transaction__description", "category__name")
    list_select_related = ("transaction", "category", "rule")
    readonly_fields = ("created_at",)


@admin.register(UserCategorizationPreference)
class UserCategorizationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "description_pattern",
        "merchant",
        "preferred_category",
        "use_count",
        "last_used",
    )
    list_filter = ("last_used", "created_at")
    search_fields = ("user__username", "description_pattern", "merchant__name")
    list_select_related = ("user", "merchant", "preferred_category")
    readonly_fields = ("created_at", "last_used")


@admin.register(CategorizationQueue)
class CategorizationQueueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "transaction_count",
        "transactions_categorized",
        "transactions_failed",
        "created_at",
        "completed_at",
        "duration",
    )
    list_filter = ("status", "created_at")
    search_fields = ("user__username",)
    readonly_fields = ("created_at", "started_at", "completed_at", "duration")
    list_select_related = ("user",)

    def transaction_count(self, obj):
        """Get count of transactions in queue."""
        return len(obj.transaction_ids) if obj.transaction_ids else 0

    transaction_count.short_description = "Transaction Count"
