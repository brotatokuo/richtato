"""Admin configuration for assistant models."""

from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ["id", "role", "content", "tool_calls", "created_at"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["title", "user__username"]
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "role", "created_at"]
    list_filter = ["role", "created_at"]
