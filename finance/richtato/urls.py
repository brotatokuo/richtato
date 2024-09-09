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
    path("login", views.login, name="login"),
    path("register", views.register, name="register"),
    path('chart/', views.chart_view, name='chart_view'),  # URL to view the chart
    path('master-chart-data/', views.master_data, name='master_data'),  # URL for chart data
    path('organize-statements', views.organize_statements, name="organize_statements"),
    path('filter-data/', views.filter_data_view, name='filter_data'),
]