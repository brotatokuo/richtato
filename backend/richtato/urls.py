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

from apps.richtato_user import views as user_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    # Admin Panel URL
    path("admin/", admin.site.urls),
    # API URLs - more specific paths
    path("api/auth/", include("apps.richtato_user.urls")),
    path("api/accounts/", include("apps.account.urls")),
    path("api/budget/", include("apps.budget.urls")),
    path("api/income/", include("apps.income.urls")),
    path("api/expense/", include("apps.expense.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/settings/", include("apps.settings.urls")),
    # Demo login for development
    path("demo-login/", user_views.demo_login, name="demo_login"),
    # Serve React app for all other routes
    path("", TemplateView.as_view(template_name="index.html")),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )

handler404 = "richtato.views.custom_404_view"
handler500 = "richtato.views.custom_500_view"
