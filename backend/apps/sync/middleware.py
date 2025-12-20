"""Middleware for automatic bank sync triggering."""

import threading
from datetime import timedelta

from django.db import models
from django.utils import timezone
from loguru import logger


class AutoSyncMiddleware:
    """Automatically trigger background sync for authenticated users with stale connections.

    This middleware checks if the user has any bank connections that haven't been
    synced recently. If so, it triggers a background sync thread that runs
    without blocking the request.

    Features:
    - Rate limiting: Won't trigger more than once per 5 minutes per user
    - Non-blocking: Request completes immediately, sync runs in background
    - Stale detection: Only syncs connections not updated in 4+ hours
    """

    # In-memory cache to prevent multiple sync triggers per session
    # Format: {user_id: last_trigger_timestamp}
    _recently_triggered: dict = {}
    _lock = threading.Lock()

    # Configuration
    TRIGGER_COOLDOWN_MINUTES = 5  # Don't trigger again within this time
    STALE_THRESHOLD_HOURS = 4  # Consider connection stale after this time

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request first (non-blocking)
        response = self.get_response(request)

        # After response is generated, check if we should sync
        try:
            if hasattr(request, "user") and request.user.is_authenticated:
                self._maybe_trigger_sync(request.user)
        except Exception as e:
            # Never let sync checking break the request
            logger.error(f"AutoSyncMiddleware error: {e}")

        return response

    def _maybe_trigger_sync(self, user):
        """Trigger sync if not recently triggered and connections are stale.

        Args:
            user: Authenticated user instance
        """
        try:
            from apps.sync.models import SyncConnection
            from apps.sync.services.background_sync_service import BackgroundSyncService

            user_id = user.id
            now = timezone.now()

            with self._lock:
                # Check if we already triggered sync recently
                last_trigger = self._recently_triggered.get(user_id)
                if last_trigger:
                    time_since = now - last_trigger
                    if time_since < timedelta(minutes=self.TRIGGER_COOLDOWN_MINUTES):
                        return  # Already triggered recently, skip

                # Check if user has any active connections that are stale
                stale_threshold = now - timedelta(hours=self.STALE_THRESHOLD_HOURS)
                has_stale = (
                    SyncConnection.objects.filter(user=user, status="active")
                    .filter(
                        models.Q(last_sync__isnull=True)
                        | models.Q(last_sync__lt=stale_threshold)
                    )
                    .exists()
                )

                if not has_stale:
                    return  # Nothing to sync

                # Mark as triggered before releasing lock
                self._recently_triggered[user_id] = now

            # Trigger background sync (outside lock to avoid holding it during I/O)
            logger.debug(f"AutoSyncMiddleware: Triggering sync for user {user_id}")
            BackgroundSyncService.trigger_user_sync(user_id)
        except Exception as e:
            logger.error(f"AutoSyncMiddleware._maybe_trigger_sync error: {e}")

    @classmethod
    def clear_trigger_cache(cls):
        """Clear the trigger cache (useful for testing)."""
        with cls._lock:
            cls._recently_triggered.clear()
