from django.urls import path

from .views import ExpenseAPIView

page_name = "expense"
urlpatterns = [
    path("api/expenses/", ExpenseAPIView.as_view()),  # GET, POST
]
