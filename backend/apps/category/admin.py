"""Admin registration for Category app."""

from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "type", "enabled")
    list_filter = ("type", "enabled")
    search_fields = ("name", "user__username")
    ordering = ("user", "name")
