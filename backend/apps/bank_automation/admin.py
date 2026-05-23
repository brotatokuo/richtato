"""Admin configuration for bank automation."""

from django.contrib import admin

from apps.bank_automation.models import (
    BankAccountLink,
    BankAutomationRun,
    BankConnection,
    BankSession,
)


@admin.register(BankConnection)
class BankConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "institution",
        "login_id",
        "status",
        "cadence",
        "preferred_run_hour_local",
        "next_run_at",
        "last_success_at",
    )
    list_filter = ("status", "cadence", "institution")
    search_fields = ("user__username", "login_id", "nickname")
    readonly_fields = (
        "created_at",
        "updated_at",
        "last_run_at",
        "last_success_at",
        "consecutive_failures",
    )


@admin.register(BankAccountLink)
class BankAccountLinkAdmin(admin.ModelAdmin):
    list_display = (
        "connection",
        "financial_account",
        "flow",
        "enabled",
        "detected_account_name",
    )
    list_filter = ("flow", "enabled")
    search_fields = ("detected_account_name", "external_account_token")


@admin.register(BankSession)
class BankSessionAdmin(admin.ModelAdmin):
    list_display = ("connection", "captured_at", "expires_at_estimated")
    readonly_fields = ("storage_state_blob",)


@admin.register(BankAutomationRun)
class BankAutomationRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "connection",
        "status",
        "started_at",
        "finished_at",
        "accounts_succeeded",
        "statements_imported",
        "triggered_by",
    )
    list_filter = ("status", "failure_kind", "triggered_by")
    readonly_fields = ("started_at", "finished_at")
