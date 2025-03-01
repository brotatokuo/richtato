from django.urls import path
from . import views

page_name = "account"
urlpatterns = [
    path("", views.main, name=page_name),
    path("add-entry/", views.add_entry, name=f"{page_name}_add_entry"),
    path("update/", views.update, name=f"{page_name}_update"),
    path(
        "get-plot-data/<int:year>/",
        views.get_plot_data,
        name=f"{page_name}_get_plot_data",
    ),
    path("get-table-data/", views.get_table_data, name=f"{page_name}_get_table_data"),
]
