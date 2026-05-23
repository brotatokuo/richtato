"""Admin configuration for bank sync."""

from django.contrib import admin

from apps.bank_sync.models import BankLogin, SyncedAccount, SyncRun


@admin.register(BankLogin)
class BankLoginAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "institution",
        "nickname",
        "status",
        "cadence",
        "preferred_run_hour_local",
        "next_run_at",
        "last_success_at",
    )
    list_filter = ("status", "cadence", "institution")
    search_fields = ("user__username", "nickname")
    readonly_fields = (
        "storage_state_encrypted",
        "cookies_captured_at",
        "cookies_expected_to_expire_at",
        "last_run_at",
        "last_success_at",
        "consecutive_failures",
        "created_at",
        "updated_at",
    )


@admin.register(SyncedAccount)
class SyncedAccountAdmin(admin.ModelAdmin):
    list_display = (
        "bank_login",
        "financial_account",
        "flow",
        "enabled",
        "detected_account_name",
    )
    list_filter = ("flow", "enabled")
    search_fields = ("detected_account_name", "external_account_token")
    readonly_fields = ("activity_url_encrypted", "created_at", "updated_at")


@admin.register(SyncRun)
class SyncRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bank_login",
        "task_kind",
        "status",
        "queued_at",
        "finished_at",
        "accounts_succeeded",
        "statements_imported",
        "triggered_by",
    )
    list_filter = ("status", "task_kind", "failure_kind", "triggered_by")
    readonly_fields = ("queued_at", "leased_at", "finished_at")
