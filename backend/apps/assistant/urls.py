"""URL configuration for assistant app."""

from django.urls import path

from . import views

urlpatterns = [
    path("chat/", views.chat, name="assistant-chat"),
    path("conversations/", views.conversation_list, name="assistant-conversations"),
    path(
        "conversations/<uuid:pk>/",
        views.conversation_detail,
        name="assistant-conversation-detail",
    ),
]
