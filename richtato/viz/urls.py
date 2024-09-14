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
    path("", views.index, name="index"),
    path("spendings", views.spendings, name="spendings"),
    path("earnings", views.earnings, name="earnings"),
    path("accounts", views.accounts, name="accounts"),
    path("login", views.login_view, name="login"),
    path("register", views.register_view, name="register"),
    path('plot-data/', views.plot_data, name='plot_data'),  # URL for chart data
    path('sql-data/', views.get_sql_data_json, name='get_sql_data_json'),
    path('import-statements-data', views.import_statements_data, name="import_statements_data"),
]