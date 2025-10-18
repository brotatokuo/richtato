from django.urls import path

from .views import IncomeAPIView, IncomeFieldChoicesView, IncomeGraphAPIView

urlpatterns = [
    path("", IncomeAPIView.as_view()),  # GET, POST
    path("<int:pk>/", IncomeAPIView.as_view()),  # GET, PATCH, DELETE
    path("field-choices/", IncomeFieldChoicesView.as_view()),  # GET, POST
    path("graph/", IncomeGraphAPIView.as_view()),  # GET
]
