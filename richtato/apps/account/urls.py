from django.urls import path

from .views import AccountAPIView, AccountFieldChoicesAPIView, AccountTransactionsAPIView

page_name = "accounts"
urlpatterns = [
    path(f"api/{page_name}/", AccountAPIView.as_view()),  # GET, POST
    path(f"api/{page_name}/<int:pk>/", AccountAPIView.as_view()),  # PUT, PATCH, DELETE
    path(
        f"api/{page_name}/field-choices/", AccountFieldChoicesAPIView.as_view()
    ),  # GET
    path(
        f"api/{page_name}/<int:pk>/transactions/", AccountTransactionsAPIView.as_view()
    ),  # GET, POST, PATCH, DELETE
]
