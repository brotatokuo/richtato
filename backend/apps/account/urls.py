from django.urls import path

from .views import (
    AccountAPIView,
    AccountDetailAPIView,
    AccountDetailFieldChoicesAPIView,
    AccountFieldChoicesAPIView,
    AccountTransactionChartView,
    AccountTransactionsAPIView,
)

urlpatterns = [
    path("", AccountAPIView.as_view()),  # GET, POST
    path("<int:pk>/", AccountAPIView.as_view()),  # PUT, PATCH, DELETE
    path("field-choices/", AccountFieldChoicesAPIView.as_view()),  # GET
    # For all accounts
    path("details/", AccountDetailAPIView.as_view()),
    path("details/field-choices/", AccountDetailFieldChoicesAPIView.as_view()),
    path("details/<int:pk>/", AccountDetailAPIView.as_view()),
    path(
        "<int:pk>/transactions/", AccountTransactionsAPIView.as_view()
    ),  # GET, POST, PATCH, DELETE
    path(
        "<int:account_id>/chart/",
        AccountTransactionChartView.as_view(),
        name="account_transaction_chart",
    ),
]
