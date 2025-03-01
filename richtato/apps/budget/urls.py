from django.urls import path
from . import views

page_name = "budget"
urlpatterns = [
    path("", views.main, name=page_name),
    path(
        "get-plot-data/<int:year>/<str:month>",
        views.get_plot_data,
        name=f"{page_name}_get_plot_data",
    ),
    path("get-table-data/", views.get_table_data, name=f"{page_name}_get_table_data"),
]
