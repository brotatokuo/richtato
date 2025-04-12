from django.urls import path

from . import views

page_name = "account"
urlpatterns = [
    path("add-entry/", views.add_entry, name=f"{page_name}_add_entry"),
    path("update/", views.update, name=f"{page_name}_update"),
]
