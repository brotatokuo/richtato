"""Admin configuration for sync."""

from django.contrib import admin

from .models import SyncConnection, SyncJob


@admin.register(SyncConnection)
class SyncConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "provider",
        "institution_name",
        "account",
        "status",
        "last_sync",
        "initial_backfill_complete",
        "created_at",
    )
    list_filter = ("provider", "status", "initial_backfill_complete", "created_at")
    search_fields = ("user__username", "institution_name", "external_account_id")
    readonly_fields = ("created_at", "updated_at", "last_sync")
    list_select_related = ("user", "account")


@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = (
        "connection",
        "status",
        "is_full_sync",
        "transactions_synced",
        "batches_processed",
        "started_at",
        "completed_at",
    )
    list_filter = ("status", "is_full_sync", "started_at")
    search_fields = ("connection__user__username", "connection__institution_name")
    readonly_fields = ("started_at", "completed_at", "duration")
    list_select_related = ("connection", "connection__user")
