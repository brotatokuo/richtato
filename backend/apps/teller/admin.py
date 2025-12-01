"""Teller admin configuration."""

from django.contrib import admin

from .models import TellerConnection


@admin.register(TellerConnection)
class TellerConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "institution_name",
        "account_name",
        "status",
        "last_sync",
        "created_at",
    )
    list_filter = ("status", "institution_name", "created_at")
    search_fields = ("user__username", "institution_name", "account_name")
    readonly_fields = ("created_at", "updated_at")
