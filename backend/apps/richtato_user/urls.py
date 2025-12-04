from django.urls import path

from . import views

urlpatterns = [
    # Authentication endpoints
    path("csrf/", views.get_csrf_token, name="csrf_token"),
    # User management endpoints
    path("get-user-id/", views.get_user_id, name="get_user_id"),
    path("profile/", views.APIProfileView.as_view(), name="profile"),
    path("check-username/", views.check_username_availability, name="check_username"),
    path("update-username/", views.update_username, name="update_username"),
    path("change-password/", views.change_password, name="change_password"),
    path("update-preferences/", views.update_preferences, name="update_preferences"),
    path("delete-account/", views.delete_account, name="delete_account"),
    # Category settings endpoint
    path(
        "category-settings/",
        views.CategorySettingsAPIView.as_view(),
        name="category_settings",
    ),
    path("preferences/", views.UserPreferenceAPIView.as_view(), name="preferences"),
    path(
        "preferences/field-choices/",
        views.UserPreferenceFieldChoicesAPIView.as_view(),
        name="preference_field_choices",
    ),
    # API Authentication endpoints (no nested 'api/' segment)
    path("login/", views.APILoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.APILogoutView.as_view(), name="logout"),
    path("demo-login/", views.APIDemoLoginView.as_view(), name="demo_login"),
]
