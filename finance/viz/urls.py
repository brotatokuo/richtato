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
from django.urls import path

from .statements import utils_import_statements
from . import views, utils, views_accounts, views_budget, views_earnings, views_settings, views_spendings


urlpatterns = [
    # Navbar
    path("", views.view_index, name="view_index"),
    path("login", views.view_login, name="view_login"),
    path("logout", views.view_logout, name="view_logout"),
    path("register", views.view_register, name="view_register"),
    path("budget", views_budget.view_budget, name="view_budget"),
    path("spendings", views_spendings.view_spendings, name="view_spendings"),
    path("earnings", views_earnings.view_earnings, name="view_earnings"),
    path("accounts", views_accounts.view_accounts, name="view_accounts"),
    path("settings", views_settings.view_settings, name="view_settings"),

    # Budget
    path('get-budget-months/', views_budget.get_budget_months, name='get_budget_months'),
    path('plot-budget-data/', views_budget.plot_budget_data, name='plot_budget_data'),
    path('get-budget-data/', views_budget.get_budget_data_json, name='get_budget_data_json'),
    path('plot-category-budget-data/', views_budget.plot_category_monthly_data, name='plot_category_monthly_data'),

    # Spendings
    path('transaction-data-spendings/', views_spendings.get_spendings_data_json, name='get_spendings_data_json'),
    path('spending-data/', views_spendings.plot_spendings_data, name='plot_spendings_data'),  
    path('add_spendings_entry', views_spendings.add_spendings_entry, name='add_spendings_entry'),
    path('get-category/', views_spendings.get_category, name='get_category'),

    # Earnings
    path('transaction-data-earnings/', views_earnings.get_earnings_data_json, name='get_earnings_data_json'),
    path('plot-earnings-data/', views_earnings.plot_earnings_data, name='plot_earnings_data'),
    path('add_earnings_entry', views_earnings.add_earnings_entry, name='add_earnings_entry'),

    # Accounts
    path('get-accounts-data/', views_accounts.get_accounts_data_json, name='get_accounts_data_json'),
    path('plot-accounts-data/', views_accounts.plot_accounts_data, name='plot_accounts_data'),
    path('plot-accounts-data-pie/', views_accounts.plot_accounts_data_pie, name='plot_accounts_data_pie'),

    # Settings
    path('get-card-settings-data/', views_settings.get_card_settings_data_json, name='get_card_settings_data_json'),
    path('get-accounts-settings-data/', views_settings.get_accounts_settings_data_json, name='get_accounts_settings_data_json'),
    path('get-categories-settings-data/', views_settings.get_categories_settings_data_json, name='get_categories_settings_data_json'),
    
    # Updating data
    path('update-spendings/', views_spendings.update_spendings, name='update_spendings'),
    path('update-earnings/', views_earnings.update_earnings, name='update_earnings'),
    path('update-accounts/', views_accounts.update_accounts, name='update_accounts'),
    path('update-settings-card-account/', views_settings.update_settings_card_account, name='update_settings_card_account'),
    path('update-settings-accounts/', views_settings.update_settings_accounts, name='update_settings_accounts'),
    path('update-settings-categories/', views_settings.update_settings_categories, name='update_settings_categories'),

    # Buttons
    path("add-account", views_accounts.add_account, name="add_account"),
    path("add-account-history", views_accounts.add_account_history, name="add_account_history"),
    path("add-card-account", views_settings.add_card_account, name="add_card_account"),
    path("add-category", views_settings.add_category, name="add_category"),

    # Utils
    path("get-user-id", utils.get_user_id, name="get_user_id"),

    # Import Spendings from CSV
    # path("import-spendings", views_spendings.import_spendings_from_csv, name="import_spendings"),
    # path("import-earnings", views_earnings.import_earnings_from_csv, name="import_earnings"),

    # Import Statements
    path("import-statements", utils_import_statements.import_statements, name="import_statements"),
    path("sort-statements-and-generate-csv", utils_import_statements.sort_statements_and_generate_csv, name="sort_statements_and_generate_csv"),
    path("test-category-search", utils_import_statements.test_category_search, name="test_category_search"),
]