"""Admin configuration for transactions."""

from django.contrib import admin

from .models import Transaction, TransactionCategory


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "type", "user", "created_at")
    list_filter = ("type", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("parent", "user")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "description",
        "amount",
        "transaction_type",
        "category",
        "account",
        "user",
        "status",
        "sync_source",
    )
    list_filter = ("transaction_type", "status", "sync_source", "date", "category")
    search_fields = ("description", "user__username", "external_id")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("user", "account", "category")
    date_hierarchy = "date"
