"""Background sync service using Python threading."""

import threading

from django.db import connection
from loguru import logger


class BackgroundSyncService:
    """Non-blocking sync using Python threading.

    This service spawns background threads to sync user connections
    without blocking the HTTP request. Works on Render free tier
    without requiring Celery or Redis.
    """

    @staticmethod
    def trigger_user_sync(user_id: int) -> None:
        """Start background sync thread for a user.

        Args:
            user_id: ID of the user to sync connections for
        """
        thread = threading.Thread(
            target=BackgroundSyncService._sync_user_connections,
            args=(user_id,),
            daemon=True,  # Daemon thread won't prevent app shutdown
        )
        thread.start()
        logger.info(f"Started background sync thread for user {user_id}")

    @staticmethod
    def _sync_user_connections(user_id: int) -> None:
        """Sync all stale connections for a user.

        Runs in a background thread. Handles database connections
        properly for threaded execution.

        Args:
            user_id: ID of the user to sync
        """
        try:
            # Close any existing connection from parent thread
            # Django will create a new one for this thread
            connection.close()

            # Import here to avoid circular imports
            from apps.richtato_user.models import User
            from apps.sync.models import SyncConnection, UserSyncStatus
            from apps.sync.services import get_sync_service

            # Get user and sync status
            user = User.objects.get(id=user_id)
            status, _ = UserSyncStatus.objects.get_or_create(user=user)

            # Mark sync as started
            status.start_sync()

            total_new = 0
            connections = SyncConnection.objects.filter(user=user, status="active")

            logger.info(f"Background sync: Found {connections.count()} active connections for user {user_id}")

            for conn in connections:
                if conn.is_stale():
                    try:
                        logger.info(f"Syncing stale connection {conn.id} ({conn.institution_name}) via {conn.provider}")
                        sync_service = get_sync_service(conn.provider)
                        result = sync_service.sync_connection(conn)
                        synced = result.get("transactions_synced", 0)
                        total_new += synced
                        logger.info(f"Connection {conn.id} synced: {synced} new transactions")
                    except Exception as e:
                        logger.error(f"Error syncing connection {conn.id}: {e}")
                        conn.mark_error(str(e))

            # Mark sync as completed
            status.complete_sync(new_transactions=total_new)
            logger.info(f"Background sync completed for user {user_id}: {total_new} new transactions")

        except Exception as e:
            logger.error(f"Background sync error for user {user_id}: {e}")
            # Try to mark status as failed
            try:
                from apps.sync.models import UserSyncStatus

                UserSyncStatus.objects.filter(user_id=user_id).update(is_syncing=False, last_error=str(e))
            except Exception:
                pass
        finally:
            # Always close the connection when thread is done
            connection.close()
