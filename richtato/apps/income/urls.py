from django.urls import path
from . import views

page_name = "income"
urlpatterns = [
    path("", views.main, name=page_name),
    path("add-entry/", views.add_entry, name=f"{page_name}_add_entry"),
    path(
        "get_recent_entries/",
        views.get_recent_entries,
        name=f"{page_name}_get_recent_entries",
    ),
    path("update/", views.update, name=f"{page_name}_update"),
    path(
        "get_line_graph_data/",
        views.get_line_graph_data,
        name=f"{page_name}_get_line_graph_data",
    ),
    path(
        "get-last-30-days/",
        views.get_last_30_days,
        name=f"{page_name}_get_last_30_days",
    ),
]
