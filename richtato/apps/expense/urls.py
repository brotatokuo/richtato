from django.urls import path

from .views import ExpenseAPIView, ExpenseFieldChoicesView

page_name = "expenses"
urlpatterns = [
    path(f"api/{page_name}/", ExpenseAPIView.as_view()),  # GET, POST
    path(f"api/{page_name}/<int:pk>/", ExpenseAPIView.as_view()),  # GET, PATCH, DELETE
    path(f"api/{page_name}/field-choices/", ExpenseFieldChoicesView.as_view()),  # GET
]
