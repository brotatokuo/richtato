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
    path("api/timeseries-data/", views.CombinedGraphAPIView.as_view()),
    path("api/card-banks/", views.CardBanksAPIView.as_view(), name="card_accounts"),
]
