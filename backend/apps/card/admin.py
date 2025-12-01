"""Admin registration for Card app."""

from django.contrib import admin
from .models import CardAccount


@admin.register(CardAccount)
class CardAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "bank")
    list_filter = ("bank",)
    search_fields = ("name", "user__username")
    ordering = ("user", "name")
