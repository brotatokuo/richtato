from django.urls import path

from .views import CardAccountAPIView, CardAccountFieldChoicesAPIView

page_name = "card-accounts"
urlpatterns = [
    path(f"api/{page_name}/", CardAccountAPIView.as_view()),  # GET, POST
    path(
        f"api/{page_name}/<int:pk>/", CardAccountAPIView.as_view()
    ),  # PUT, PATCH, DELETE
    path(
        f"api/{page_name}/field-choices/", CardAccountFieldChoicesAPIView.as_view()
    ),  # GET
]
