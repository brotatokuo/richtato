from django.urls import path

from .views import (
    AccountAPIView,
    AccountDetailAPIView,
    AccountDetailFieldChoicesAPIView,
    AccountFieldChoicesAPIView,
    AccountTransactionsAPIView,
    AccountTransactionChartView,
)

page_name = "accounts"
urlpatterns = [
    path(f"api/{page_name}/", AccountAPIView.as_view()),  # GET, POST
    path(f"api/{page_name}/<int:pk>/", AccountAPIView.as_view()),  # PUT, PATCH, DELETE
    path(
        f"api/{page_name}/field-choices/", AccountFieldChoicesAPIView.as_view()
    ),  # GET
    # For all accounts
    path(f"api/{page_name}/details/", AccountDetailAPIView.as_view()),
    path(
        f"api/{page_name}/details/field-choices/",
        AccountDetailFieldChoicesAPIView.as_view(),
    ),
    path(f"api/{page_name}/details/<int:pk>/", AccountDetailAPIView.as_view()),
    path(
        f"api/{page_name}/<int:pk>/transactions/", AccountTransactionsAPIView.as_view()
    ),  # GET, POST, PATCH, DELETE
    path(
        f"{page_name}/<int:account_id>/chart/",
        AccountTransactionChartView.as_view(),
        name="account_transaction_chart",
    ),
]
