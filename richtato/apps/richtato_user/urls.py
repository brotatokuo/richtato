from django.urls import path

from . import views
from apps.expense.views import add_entry

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("welcome/", views.welcome, name="welcome"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("get-user-id/", views.get_user_id, name="get_user_id"),
    path("friends/", views.friends, name="friends"),
    path("files/", views.files, name="files"),
    path("goals/", views.goals, name="goals"),
    path("profile/", views.profile, name="profile"),
    path("temp-input/", views.temp_input, name="temp_input"),
    path("temp-input/add-entry/", add_entry, name="add_entry"),
    path("user_settings/", views.user_settings, name="user_settings"),
    path("account_settings/", views.account_settings, name="account_settings"),

]
