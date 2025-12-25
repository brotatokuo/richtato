from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.richtato_user.models import User, UserPreference


class UserAdmin(BaseUserAdmin):
    """Custom User admin with password change support."""

    list_display = ("username", "email", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active", "is_demo")
    search_fields = ("username", "email")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")

    # Fields shown when editing an existing user
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("email",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Demo", {"fields": ("is_demo", "demo_expires_at")}),
        ("Import", {"fields": ("import_path",)}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Fields shown when creating a new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )


admin.site.register(User, UserAdmin)
admin.site.register(UserPreference)
