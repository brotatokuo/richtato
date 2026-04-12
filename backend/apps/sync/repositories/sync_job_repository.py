"""Repository for SyncJob model."""

from apps.sync.models import SyncConnection, SyncJob


class SyncJobRepository:
    """Repository for sync job data access."""

    def get_by_id(self, job_id: int) -> SyncJob | None:
        """Get job by ID."""
        try:
            return SyncJob.objects.select_related("connection").get(id=job_id)
        except SyncJob.DoesNotExist:
            return None

    def get_by_connection(self, connection: SyncConnection, limit: int = 50) -> list[SyncJob]:
        """Get jobs for a connection."""
        return list(SyncJob.objects.filter(connection=connection).order_by("-started_at")[:limit])

    def get_running_jobs(self, connection: SyncConnection = None) -> list[SyncJob]:
        """Get currently running jobs."""
        queryset = SyncJob.objects.filter(status="running").select_related("connection")
        if connection:
            queryset = queryset.filter(connection=connection)
        return list(queryset.all())

    def create_job(self, connection: SyncConnection, is_full_sync: bool = False) -> SyncJob:
        """Create a new sync job."""
        job = SyncJob.objects.create(connection=connection, is_full_sync=is_full_sync, status="running")
        return job

    def get_recent_jobs(self, limit: int = 100) -> list[SyncJob]:
        """Get recent jobs across all connections."""
        return list(SyncJob.objects.select_related("connection", "connection__user").order_by("-started_at")[:limit])
