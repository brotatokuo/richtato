from django.urls import path

from .views import (
    CategorizeTransactionView,
    ExpenseAPIView,
    ExpenseFieldChoicesView,
    ExpenseGraphAPIView,
    ImportStatementsView,
)

urlpatterns = [
    path("", ExpenseAPIView.as_view()),  # GET, POST
    path("<int:pk>/", ExpenseAPIView.as_view()),  # GET, PATCH, DELETE
    path("field-choices/", ExpenseFieldChoicesView.as_view()),  # GET
    path("graph/", ExpenseGraphAPIView.as_view()),  # GET
    path("categorize-transaction/", CategorizeTransactionView.as_view()),  # Post
    path("import-statements/", ImportStatementsView.as_view()),  # Post
]
