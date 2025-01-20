"""
URL configuration for richtato project.

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

urlpatterns = [
    # Admin Panel URL
    path("admin/", admin.site.urls),
    # Core user management (login, register, etc.)
    path("", include("apps.richtato_user.urls")),
    # Feature-specific URLs
    path("account/", include("apps.account.urls")),
    path("budget/", include("apps.budget.urls")),
    path("income/", include("apps.income.urls")),
    path("expense/", include("apps.expense.urls")),
    path("settings/", include("apps.settings.urls")),
]
