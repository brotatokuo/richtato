from django.urls import path

from .views import (
    ExpenseAPIView,
    ExpenseFieldChoicesView,
    ExpenseGraphAPIView,
    CategorizeTransactionView,
    ImportStatementsView,
)

page_name = "expenses"
urlpatterns = [
    path(f"api/{page_name}/", ExpenseAPIView.as_view()),  # GET, POST
    path(f"api/{page_name}/<int:pk>/", ExpenseAPIView.as_view()),  # GET, PATCH, DELETE
    path(f"api/{page_name}/field-choices/", ExpenseFieldChoicesView.as_view()),  # GET
    path(f"api/{page_name}/graph/", ExpenseGraphAPIView.as_view()),  # GET
    path(
        f"api/{page_name}/categorize-transaction/", CategorizeTransactionView.as_view()
    ),  # Post
    path(f"api/{page_name}/import-statements/", ImportStatementsView.as_view()),  # Post
]
