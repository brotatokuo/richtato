from django.urls import path

from .views import CardAccountAPIView

urlpatterns = [
    path("api/card-accounts/", CardAccountAPIView.as_view()),  # GET, POST
    path(
        "api/card-accounts/<int:pk>/", CardAccountAPIView.as_view()
    ),  # PUT, PATCH, DELETE
]
