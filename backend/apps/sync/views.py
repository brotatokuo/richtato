"""Views for sync API."""

from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.financial_account.services.account_service import AccountService
from apps.sync.repositories.sync_connection_repository import SyncConnectionRepository
from apps.sync.repositories.sync_job_repository import SyncJobRepository
from apps.sync.serializers import (
    SyncConnectionCreateSerializer,
    SyncConnectionSerializer,
    SyncJobSerializer,
)
from apps.sync.services.teller_sync_service import TellerSyncService
from loguru import logger


class SyncConnectionListCreateAPIView(APIView):
    """List all sync connections or create a new one."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection_repository = SyncConnectionRepository()
        self.account_service = AccountService()

    def get(self, request):
        """List all sync connections for the user."""
        connections = self.connection_repository.get_by_user(request.user)
        serializer = SyncConnectionSerializer(connections, many=True)
        return Response({"connections": serializer.data})

    def post(self, request):
        """Create a new Teller sync connection."""
        serializer = SyncConnectionCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get account
            account = self.account_service.get_account_by_id(
                serializer.validated_data["account_id"], request.user
            )
            if not account:
                return Response(
                    {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Create connection
            connection = self.connection_repository.create_connection(
                user=request.user,
                account=account,
                provider="teller",
                access_token=serializer.validated_data["access_token"],
                institution_name=serializer.validated_data["institution_name"],
                external_account_id=serializer.validated_data["external_account_id"],
                external_enrollment_id=serializer.validated_data.get(
                    "external_enrollment_id", ""
                ),
            )

            response_serializer = SyncConnectionSerializer(connection)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating sync connection: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SyncConnectionDetailAPIView(APIView):
    """Retrieve or delete a sync connection."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection_repository = SyncConnectionRepository()

    def get(self, request, pk):
        """Get connection details."""
        connection = self.connection_repository.get_by_id(pk)

        if not connection or connection.user != request.user:
            return Response(
                {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = SyncConnectionSerializer(connection)
        return Response(serializer.data)

    def delete(self, request, pk):
        """Disconnect/delete connection."""
        connection = self.connection_repository.get_by_id(pk)

        if not connection or connection.user != request.user:
            return Response(
                {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            self.connection_repository.delete_connection(connection)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error deleting connection {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SyncTriggerAPIView(APIView):
    """Trigger sync for a connection."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection_repository = SyncConnectionRepository()
        self.sync_service = TellerSyncService()

    def post(self, request, pk):
        """Trigger sync."""
        connection = self.connection_repository.get_by_id(pk)

        if not connection or connection.user != request.user:
            return Response(
                {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if full sync is requested
        force_full_sync = request.data.get("full_sync", False)
        if isinstance(force_full_sync, str):
            force_full_sync = force_full_sync.lower() in ["true", "1", "yes"]

        logger.info(
            f"Starting sync for connection {pk}, user {request.user.username}, "
            f"force_full_sync={force_full_sync}"
        )

        try:
            result = self.sync_service.sync_connection(
                connection, force_full_sync=force_full_sync
            )
            return Response(result)

        except Exception as e:
            logger.error(f"Error syncing connection {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SyncJobListAPIView(APIView):
    """List sync jobs for a connection."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection_repository = SyncConnectionRepository()
        self.job_repository = SyncJobRepository()

    def get(self, request, pk):
        """Get sync job history for a connection."""
        connection = self.connection_repository.get_by_id(pk)

        if not connection or connection.user != request.user:
            return Response(
                {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
            )

        jobs = self.job_repository.get_by_connection(connection)
        serializer = SyncJobSerializer(jobs, many=True)
        return Response({"jobs": serializer.data})
