from django.urls import path

from .views import AccountAPIView, AccountFieldChoicesAPIView

urlpatterns = [
    path("api/accounts/", AccountAPIView.as_view()),  # GET, POST
    path("api/accounts/<int:pk>/", AccountAPIView.as_view()),  # PUT, PATCH, DELETE
    path("api/accounts/field-choices/", AccountFieldChoicesAPIView.as_view()),  # GET
]
