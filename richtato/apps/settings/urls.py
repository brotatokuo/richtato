from django.urls import path

from . import views

page_name = "settings"
urlpatterns = [
    path("", views.main, name=page_name),
    # Card Account
    path("get-cards/", views.get_cards, name=f"{page_name}_get_cards"),
    path("add-card/", views.add_card, name=f"{page_name}_add_card"),
    path("update-cards/", views.update_cards, name=f"{page_name}_update_cards"),
]
