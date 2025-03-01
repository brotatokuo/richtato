from django.urls import path

from . import views

page_name = "expense"
urlpatterns = [
    path("", views.main, name=page_name),
    path("add-entry/", views.add_entry, name=f"{page_name}_add_entry"),
    path("update/", views.update, name=f"{page_name}_update"),
    path("get-plot-data/", views.get_plot_data, name=f"{page_name}_get_plot_data"),
    path("get-table-data/", views.get_table_data, name=f"{page_name}_get_table_data"),
    path(
        "get-full-table-data/",
        views.get_full_table_data,
        name=f"{page_name}_get_full_table_data",
    ),
    path("guess-category/", views.guess_category, name=f"{page_name}_guess_category"),
    path(
        "get-monthly-diff/", views.get_monthly_diff, name=f"{page_name}_get_monthly_dff"
    ),
]
