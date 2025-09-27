from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .views import CustomPasswordResetConfirmView, CustomPasswordResetView

urlpatterns = [
    # Removed empty path - this is now API-only
    # path("", views.index, name="index"),
    # path("dashboard/", views.dashboard, name="dashboard"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("get-user-id/", views.get_user_id, name="get_user_id"),
    path("upload/", views.upload, name="upload"),
    path("profile/", views.profile, name="profile"),
    path("input/", views.input, name="input"),
    path("user_settings/", views.user_settings, name="user_settings"),
    path("account-settings/", views.account_settings, name="account_settings"),
    path("table/", views.table, name="table"),
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
    path(
        "api/check-username/", views.check_username_availability, name="check_username"
    ),
    path("api/update-username/", views.update_username, name="update_username"),
    path("api/change-password/", views.change_password, name="change_password"),
    path(
        "api/update-preferences/", views.update_preferences, name="update_preferences"
    ),
    path("api/delete-account/", views.delete_account, name="delete_account"),
]

urlpatterns += [
    path("password-reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
