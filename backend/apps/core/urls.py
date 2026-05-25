from django.urls import path

from . import views

urlpatterns = [
    path("notifications/", views.InAppNotificationListAPIView.as_view(), name="notification-list"),
    path("notifications/<int:pk>/", views.InAppNotificationDetailAPIView.as_view(), name="notification-detail"),
    path(
        "notifications/mark-all-read/",
        views.InAppNotificationMarkAllReadAPIView.as_view(),
        name="notification-mark-all-read",
    ),
]
