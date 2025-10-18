from django.urls import path

from .views import CardAccountAPIView, CardAccountFieldChoicesAPIView

page_name = "card-accounts"
urlpatterns = [
    path(f"{page_name}/", CardAccountAPIView.as_view()),  # GET, POST
    path(f"{page_name}/<int:pk>/", CardAccountAPIView.as_view()),  # PUT, PATCH, DELETE
    path(
        f"{page_name}/field-choices/", CardAccountFieldChoicesAPIView.as_view()
    ),  # GET
]
