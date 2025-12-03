"""Admin configuration for transactions."""

from django.contrib import admin

from .models import Merchant, Transaction, TransactionCategory


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_income", "is_expense", "user", "created_at")
    list_filter = ("is_income", "is_expense", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("parent", "user")


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("name", "category_hint", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("category_hint",)


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
    list_select_related = ("user", "account", "category", "merchant")
    date_hierarchy = "date"
