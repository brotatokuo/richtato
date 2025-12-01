"""Teller API views."""

from apps.teller.models import TellerConnection
from apps.teller.serializers import (
    TellerConnectionCreateSerializer,
    TellerConnectionSerializer,
    TellerSyncResponseSerializer,
)
from apps.teller.services.sync_service import TellerSyncService
from apps.teller.services.teller_service import TellerService
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class TellerConnectionAPIView(APIView):
    """API view for Teller connections."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.teller_service = TellerService()

    def get(self, request):
        """List all Teller connections for the authenticated user."""
        connections = self.teller_service.get_connections_for_user(request.user)
        serializer = TellerConnectionSerializer(connections, many=True)

        return Response(
            {
                "columns": [
                    {"field": "id", "title": "ID"},
                    {"field": "institution_name", "title": "Institution"},
                    {"field": "account_name", "title": "Account"},
                    {"field": "status", "title": "Status"},
                    {"field": "last_sync", "title": "Last Sync"},
                ],
                "rows": serializer.data,
            }
        )

    def post(self, request):
        """Create a new Teller connection."""
        serializer = TellerConnectionCreateSerializer(data=request.data)

        if not serializer.is_valid():
            logger.error(f"Invalid Teller connection data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            connection = self.teller_service.create_connection(
                user=request.user,
                access_token=serializer.validated_data["access_token"],
                teller_account_id=serializer.validated_data["teller_account_id"],
                institution_name=serializer.validated_data["institution_name"],
                account_name=serializer.validated_data["account_name"],
                enrollment_id=serializer.validated_data.get("enrollment_id", ""),
                account_type=serializer.validated_data.get("account_type", ""),
            )

            response_serializer = TellerConnectionSerializer(connection)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating Teller connection: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """Disconnect a Teller connection."""
        try:
            result = self.teller_service.disconnect_connection(pk, request.user)
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error disconnecting Teller connection {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class TellerSyncAPIView(APIView):
    """API view for syncing Teller transactions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.teller_service = TellerService()
        self.sync_service = TellerSyncService()

    def post(self, request, pk):
        """Trigger sync for a specific Teller connection."""
        connection = self.teller_service.get_connection_by_id(pk, request.user)

        if not connection:
            return Response(
                {"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get number of days to sync (default 30)
        days = request.data.get("days", 30)

        try:
            days = int(days)
            if days < 1 or days > 365:
                days = 30
        except (ValueError, TypeError):
            days = 30

        logger.info(
            f"Starting sync for connection {pk}, user {request.user.username}, "
            f"days={days}"
        )

        # Perform sync
        result = self.sync_service.sync_connection(connection, days=days)

        # Serialize and return result
        serializer = TellerSyncResponseSerializer(data=result)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(result)
