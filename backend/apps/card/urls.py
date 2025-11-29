"""Card account URL configuration."""

from django.urls import path

from .views import CardAccountAPIView, CardAccountFieldChoicesAPIView

urlpatterns = [
    path("", CardAccountAPIView.as_view()),  # GET, POST
    path("<int:pk>/", CardAccountAPIView.as_view()),  # PUT, PATCH, DELETE
    path("field-choices/", CardAccountFieldChoicesAPIView.as_view()),  # GET
]
