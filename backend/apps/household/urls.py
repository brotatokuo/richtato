"""URLs for household API."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.HouseholdAPIView.as_view(), name="household-detail"),
    path("invite/", views.HouseholdInviteAPIView.as_view(), name="household-invite"),
    path("join/", views.HouseholdJoinAPIView.as_view(), name="household-join"),
    path("leave/", views.HouseholdLeaveAPIView.as_view(), name="household-leave"),
    path("members/", views.HouseholdMembersAPIView.as_view(), name="household-members"),
]
