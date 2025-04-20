from django.urls import path

from .views import ExpenseAPIView

page_name = "expenses"
urlpatterns = [
    path(f"api/{page_name}/", ExpenseAPIView.as_view()),  # GET, POST
    path(f"api/{page_name}/<int:pk>/", ExpenseAPIView.as_view()),  # GET, PATCH, DELETE
]
