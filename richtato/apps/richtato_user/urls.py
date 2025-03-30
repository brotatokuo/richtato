from django.urls import path

from richtato.apps.expense import views as expense
from richtato.apps.income import views as income

from . import views

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
    path("input/", views.input, name="input"),
    path("input/add-expense/", expense.add_entry, name="add_expense"),
    path("input/add-income/", income.add_entry, name="add_income"),
    path("user_settings/", views.user_settings, name="user_settings"),
    path("account_settings/", views.account_settings, name="account_settings"),
    path("table/", views.table, name="table"),
    path("get-table-data/", views.get_table_data, name="get_table_data"),
    path("timeseries-plots/", views.timeseries_plots, name="timeseries_plots"),
    path("get-timeseries-data/", views.get_timeseries_data, name="get_timeseries_data"),
    path("get-card-types/", views.get_card_types, name="get_card_types"),
]

# if settings.DEBUG:
#     import debug_toolbar

#     urlpatterns = [
#         path("__debug__/", include(debug_toolbar.urls)),
#     ] + urlpatterns
#     ] + urlpatterns
#     ] + urlpatterns
