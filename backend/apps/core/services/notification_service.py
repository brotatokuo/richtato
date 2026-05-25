"""In-app and email notification helpers."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone
from loguru import logger

from apps.core.models import InAppNotification
from apps.core.services.email_service import EmailService
from apps.richtato_user.models import User, UserPreference

BANK_SYNC_DEDUPE_MINUTES = 60


class NotificationService:
    """Create account-controlled notifications with bank-sync deduping."""

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

    def notify_bank_sync_failure(
        self,
        *,
        user: User,
        title: str,
        body: str,
        severity: str = "error",
        source_key: str,
        metadata: dict[str, Any] | None = None,
        action_url: str = "/bank-agent",
    ) -> InAppNotification | None:
        preference, _ = UserPreference.objects.get_or_create(user=user)
        if self._recent_duplicate(user=user, source_key=source_key):
            logger.info("Skipping duplicate bank-sync notification user={} key={}", user.id, source_key)
            return None

        notification = None
        if preference.notifications_enabled and preference.bank_sync_in_app_notifications:
            notification = self.create_in_app(
                user=user,
                title=title,
                body=body,
                severity=severity,
                source="bank_sync",
                source_key=source_key,
                action_url=action_url,
                metadata=metadata,
            )

        if (
            preference.notifications_enabled
            and preference.bank_sync_email_notifications
            and user.email
            and EmailService.is_configured()
        ):
            EmailService.send(
                to=user.email,
                subject=f"Richtato bank sync needs attention: {title}",
                text=f"{body}\n\nOpen Richtato: {action_url}",
                html=f'<p>{body}</p><p><a href="{action_url}">Open Richtato</a></p>',
            )

        return notification

    def _recent_duplicate(self, *, user: User, source_key: str) -> bool:
        since = timezone.now() - timedelta(minutes=BANK_SYNC_DEDUPE_MINUTES)
        return InAppNotification.objects.filter(
            user=user,
            source="bank_sync",
            source_key=source_key,
            created_at__gte=since,
        ).exists()
