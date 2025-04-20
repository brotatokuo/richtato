from django.urls import path

from .views import IncomeAPIView

page_name = "incomes"
urlpatterns = [
    path(f"api/{page_name}/", IncomeAPIView.as_view()),  # GET, POST
    path(f"api/{page_name}/<int:pk>/", IncomeAPIView.as_view()),  # GET, PATCH, DELETE
]
