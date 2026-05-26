"""Core API views."""

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import InAppNotification
from apps.core.serializers import InAppNotificationSerializer


class InAppNotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_only = request.query_params.get("unread") == "1"
        limit = min(int(request.query_params.get("limit", "20")), 100)
        queryset = InAppNotification.objects.filter(user=request.user)
        if unread_only:
            queryset = queryset.filter(read_at__isnull=True)
        rows = list(queryset[:limit])
        serializer = InAppNotificationSerializer(rows, many=True)
        unread_count = InAppNotification.objects.filter(user=request.user, read_at__isnull=True).count()
        return Response({"notifications": serializer.data, "unread_count": unread_count})


class InAppNotificationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notification = InAppNotification.objects.filter(user=request.user, pk=pk).first()
        if notification is None:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
        if request.data.get("read") is True and notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
        serializer = InAppNotificationSerializer(notification)
        return Response(serializer.data)


class InAppNotificationMarkAllReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = InAppNotification.objects.filter(user=request.user, read_at__isnull=True).update(
            read_at=timezone.now()
        )
        return Response({"updated": updated})
