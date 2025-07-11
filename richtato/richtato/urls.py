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
from django.urls import include, path

from richtato.apps.richtato_user import views as user_views

urlpatterns = [
    # Admin Panel URL
    path("admin/", admin.site.urls),
    # Core user management (login, register, etc.)
    path("", include("apps.richtato_user.urls")),
    # Feature-specific URLs
    path("", include("richtato.apps.account.urls")),
    path("", include("richtato.apps.budget.urls")),
    path("", include("richtato.apps.income.urls")),
    path("", include("richtato.apps.expense.urls")),
    path("dashboard/", include("richtato.apps.dashboard.urls")),
    path("", include("apps.settings.urls")),
    path("demo-login/", user_views.demo_login, name="demo_login"),
]

handler404 = "richtato.richtato.views.custom_404_view"
handler500 = "richtato.richtato.views.custom_500_view"
