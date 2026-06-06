"""In-app notification helpers."""

from __future__ import annotations

from typing import Any

from apps.core.models import InAppNotification
from apps.richtato_user.models import User


class NotificationService:
    """Create account-controlled in-app notifications."""

    def create_in_app(
        self,
        *,
        user: User,
        title: str,
        body: str = "",
        severity: str = "info",
        source: str = "system",
        source_key: str = "",
        action_url: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> InAppNotification:
        return InAppNotification.objects.create(
            user=user,
            title=title,
            body=body,
            severity=severity,
            source=source,
            source_key=source_key,
            action_url=action_url,
            metadata=metadata or {},
        )
