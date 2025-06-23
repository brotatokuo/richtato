from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("get-user-id/", views.get_user_id, name="get_user_id"),
    path("friends/", views.friends, name="friends"),
    path("files/", views.files, name="files"),
    path("goals/", views.goals, name="goals"),
    path("profile/", views.profile, name="profile"),
    path("input/", views.input, name="input"),
    path("user_settings/", views.user_settings, name="user_settings"),
    path("account-settings/", views.account_settings, name="account_settings"),
    path("table/", views.table, name="table"),
    path("timeseries-graph/", views.timeseries_graph, name="timeseries_graph"),
    path("assets/", views.assets, name="assets"),
    path(
        "api/timeseries-data/",
        views.CombinedGraphAPIView.as_view(),
        name="timeseries_data_api",
    ),
    path("api/categories/", views.CategoryView.as_view(), name="categories_api"),
    path(
        "api/categories/<int:pk>/",
        views.CategoryView.as_view(),
        name="category_detail_api",
    ),  # PUT, PATCH, DELETE
    path(
        "api/categories/field-choices/",
        views.CategoryFieldChoicesAPIView.as_view(),
        name="category_field_choices_api",
    ),  # GET
]
