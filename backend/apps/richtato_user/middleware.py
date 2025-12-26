"""Middleware for user-related functionality."""

import threading
import time

from django.db import close_old_connections
from django.utils import timezone
from loguru import logger

from .models import User


class CleanupDemoUsersMiddleware:
    """Middleware that periodically cleans up expired demo users."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.keep_running = True
        self.thread = threading.Thread(target=self.cleanup_periodically)
        self.thread.daemon = True
        self.thread.start()

    def cleanup_periodically(self):
        while self.keep_running:
            try:
                close_old_connections()  # Ensure DB connection is usable in this thread
                now = timezone.now()
                expired_users = User.objects.filter(
                    is_demo=True, demo_expires_at__lt=now
                )
                count = expired_users.count()
                if count:
                    expired_users.delete()
                    logger.info(f"Deleted {count} expired demo users at {now}")
            except Exception as e:
                logger.error(f"Error during demo user cleanup: {e}")
            # Wait for 10 minutes (600 seconds) before next cleanup
            time.sleep(600)

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def stop_cleanup(self):
        self.keep_running = False
        if self.thread.is_alive():
            self.thread.join()
