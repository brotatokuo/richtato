"""Core app models."""

from django.conf import settings
from django.db import models


class InAppNotification(models.Model):
    """User-visible notification created by backend services."""

    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("success", "Success"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="in_app_notifications")
    source = models.CharField(max_length=64, default="system")
    source_key = models.CharField(max_length=255, blank=True, default="")
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="info")
    title = models.CharField(max_length=160)
    body = models.TextField(blank=True, default="")
    action_url = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "read_at", "-created_at"]),
            models.Index(fields=["user", "source", "source_key", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user_id}: {self.title}"
