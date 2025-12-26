"""Admin configuration for financial accounts."""

from django.contrib import admin

from .models import AccountBalanceHistory, FinancialAccount, FinancialInstitution


@admin.register(FinancialInstitution)
class FinancialInstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "account_type",
        "institution",
        "balance",
        "is_active",
        "sync_source",
        "created_at",
    )
    list_filter = ("account_type", "sync_source", "is_active", "created_at")
    search_fields = ("name", "user__username", "account_number_last4")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("user", "institution")


@admin.register(AccountBalanceHistory)
class AccountBalanceHistoryAdmin(admin.ModelAdmin):
    list_display = ("account", "date", "balance", "created_at")
    list_filter = ("date", "created_at")
    search_fields = ("account__name",)
    readonly_fields = ("created_at",)
    list_select_related = ("account",)
