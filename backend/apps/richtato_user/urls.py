from django.urls import path

from . import views

urlpatterns = [
    # Authentication endpoints
    path("csrf/", views.get_csrf_token, name="csrf_token"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # User management endpoints
    path("get-user-id/", views.get_user_id, name="get_user_id"),
    path("profile/", views.APIProfileView.as_view(), name="profile"),
    path("check-username/", views.check_username_availability, name="check_username"),
    path("update-username/", views.update_username, name="update_username"),
    path("change-password/", views.change_password, name="change_password"),
    path("update-preferences/", views.update_preferences, name="update_preferences"),
    path("delete-account/", views.delete_account, name="delete_account"),
    # Data endpoints
    path(
        "timeseries-data/", views.CombinedGraphAPIView.as_view(), name="timeseries_data"
    ),
    path("categories/", views.CategoryView.as_view(), name="categories"),
    path("categories/<int:pk>/", views.CategoryView.as_view(), name="category_detail"),
    path(
        "categories/field-choices/",
        views.CategoryFieldChoicesAPIView.as_view(),
        name="category_field_choices",
    ),
    path(
        "category-settings/",
        views.CategorySettingsAPIView.as_view(),
        name="category_settings",
    ),
    path("card-accounts/", views.CardBanksAPIView.as_view(), name="card_accounts"),
    # API Authentication endpoints
    path("api/login/", views.APILoginView.as_view(), name="api_login"),
    path("api/logout/", views.APILogoutView.as_view(), name="api_logout"),
    path("api/profile/", views.APIProfileView.as_view(), name="api_profile"),
    path("api/demo-login/", views.APIDemoLoginView.as_view(), name="api_demo_login"),
]
