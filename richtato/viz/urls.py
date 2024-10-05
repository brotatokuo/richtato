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
    path("", views.view_index, name="view_index"),
    path("login", views.view_login, name="view_login"),
    path("logout", views.view_logout, name="view_logout"),
    path("register", views.view_register, name="view_register"),
    path("spendings", views.view_spendings, name="view_spendings"),
    path("earnings", views.view_earnings, name="view_earnings"),
    path("accounts", views.view_accounts, name="view_accounts"),
    path("settings", views.view_settings, name="view_settings"),

    # Spendings
    path('transaction-data-spendings/', views.get_transaction_data_json_spendings, name='get_transaction_data_json_spendings'),
    path('spending-data/', views.plot_spendings_data, name='plot_spending_data'),  
    path('add_spendings_entry', views.add_spendings_entry, name='add_spendings_entry'),

    # Earnings
    path('transaction-data-earnings/', views.get_transaction_data_json_earnings, name='get_transaction_data_json_earnings'),
    path('plot-earnings-data/', views.plot_earnings_data, name='plot_earnings_data'),
    path('add_earnings_entry', views.add_earnings_entry, name='add_earnings_entry'),

    # Accounts
    path('get-accounts-data/', views.get_accounts_data_json, name='get_accounts_data_json'),
    path('plot-accounts-data/', views.plot_accounts_data, name='plot_accounts_data'),
    path('plot-accounts-data-pie/', views.plot_accounts_data_pie, name='plot_accounts_data_pie'),

    # Data Import/ Export
    path('export-statements-data', views.export_statements_data, name="export_statements_data"),
    path('import-statements-data', views.import_statements_data, name="import_statements_data"),

    # Updating data
    path('update-row/', views.update_row, name='update_row'),
    path('delete-row/', views.delete_row, name='delete_row'),
    path("update-accounts", views.update_accounts, name="update_accounts"),

    # Buttons
    path("add-account", views.add_account, name="add_account"),
    path("add-card-account", views.add_card_account, name="add_card_account"),
]