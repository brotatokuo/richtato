from django.urls import path

from .views import CardAccountAPIView, CardAccountFieldChoicesAPIView

urlpatterns = [
    path("api/card-accounts/", CardAccountAPIView.as_view()),  # GET, POST
    path(
        "api/card-accounts/<int:pk>/", CardAccountAPIView.as_view()
    ),  # PUT, PATCH, DELETE
    path(
        "api/card-accounts/field-choices/", CardAccountFieldChoicesAPIView.as_view()
    ),  # GET
]
