"""
URL configuration for finance project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    # Navbar
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register_view, name="register"),
    path("spendings", views.spendings, name="spendings"),
    path("earnings", views.earnings, name="earnings"),
    path("accounts", views.accounts, name="accounts"),
    path("settings", views.settings, name="settings"),

    # Buttons
    path("add-account", views.add_account, name="add_account"),
    path("add-card-account", views.add_card_account, name="add_card_account"),

    # Plotting
    path('plot-spending-data/', views.plot_spendings_data, name='plot_spending_data'),
    path('plot-earnings-data/', views.plot_earnings_data, name='plot_earnings_data'),
    path('sql-data/', views.get_sql_data_json, name='get_sql_data_json'),
    path('sql-data_earnings/', views.get_sql_data_json_earnings, name='get_sql_data_json_earnings'),
    path('plot-accounts-data/', views.plot_accounts_data, name='plot_accounts_data'),
    path('plot-accounts-data-pie/', views.plot_accounts_data_pie, name='plot_accounts_data_pie'),
    path('get-accounts-data/', views.get_accounts_data_json, name='get_accounts_data_json'),

    # Manual data entry
    path('spending_data_entry', views.spending_data_entry, name='spending_data_entry'),
    path('earnings_data_entry', views.earnings_data_entry, name='earnings_data_entry'),

    # Data Import/ Export
    path("data", views.data, name="data"),
    path('export-statements-data', views.export_statements_data, name="export_statements_data"),
    path('import-statements-data', views.import_statements_data, name="import_statements_data"),

    # Updating data
    path('update-row/', views.update_row, name='update_row'),
    path('delete-row/', views.delete_row, name='delete_row'),
    path("update-accounts", views.update_accounts, name="update_accounts"),
]