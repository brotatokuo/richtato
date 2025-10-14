from django.urls import path

from .views import IncomeAPIView, IncomeFieldChoicesView, IncomeGraphAPIView

# These routes are included under '/api/income/' from the project urls
urlpatterns = [
    path("", IncomeAPIView.as_view()),  # GET, POST at /api/income/
    path("<int:pk>/", IncomeAPIView.as_view()),  # GET, PATCH, DELETE
    path("field-choices/", IncomeFieldChoicesView.as_view()),  # GET
    path("graph/", IncomeGraphAPIView.as_view()),  # GET
]
