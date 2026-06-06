"""Serializers for core API models."""

from rest_framework import serializers

from apps.core.models import InAppNotification


class InAppNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InAppNotification
        fields = [
            "id",
            "source",
            "source_key",
            "severity",
            "title",
            "body",
            "action_url",
            "metadata",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields
