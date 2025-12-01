"""Teller URL configuration."""

from django.urls import path

from .views import TellerConnectionAPIView, TellerSyncAPIView

urlpatterns = [
    path("connections/", TellerConnectionAPIView.as_view(), name="teller_connections"),
    path(
        "connections/<int:pk>/",
        TellerConnectionAPIView.as_view(),
        name="teller_connection_detail",
    ),
    path("sync/<int:pk>/", TellerSyncAPIView.as_view(), name="teller_sync"),
]
