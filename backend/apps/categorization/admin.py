"""Admin configuration for categorization."""

from django.contrib import admin

from .models import (
    CategorizationHistory,
    CategorizationQueue,
)


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
    list_select_related = ("transaction", "category")
    readonly_fields = ("created_at",)


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
