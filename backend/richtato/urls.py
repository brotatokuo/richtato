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
from apps.sync import views as sync_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Richtato API",
        default_version="v1",
        description="Personal Finance Management API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@richtato.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin Panel URL
    path("admin/", admin.site.urls),
    # API Documentation
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "api/docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # New Unified API URLs
    path("api/accounts/", include("apps.financial_account.urls")),
    path("api/transactions/", include("apps.transaction.urls")),
    path("api/sync/", include("apps.sync.urls")),
    path("api/budgets/", include("apps.budget.urls")),
    # V1 API URLs (for frontend compatibility)
    path("api/v1/accounts/", include("apps.financial_account.urls")),
    path("api/v1/card-accounts/", include("apps.financial_account.urls_card_accounts")),
    path("api/v1/transactions/", include("apps.transaction.urls")),
    path("api/v1/teller/", include("apps.sync.urls")),
    path("api/v1/budgets/", include("apps.budget.urls")),
    # Auth and User management
    path("api/auth/", include("apps.richtato_user.urls")),
    path("api/v1/auth/", include("apps.richtato_user.urls")),
    # Dashboard endpoints
    path("api/budget-dashboard/", include("apps.budget_dashboard.urls")),
    path("api/asset-dashboard/", include("apps.asset_dashboard.urls")),
    path("api/v1/budget-dashboard/", include("apps.budget_dashboard.urls")),
    path("api/v1/asset-dashboard/", include("apps.asset_dashboard.urls")),
    # Demo login for development
    path("demo-login/", user_views.demo_login, name="demo_login"),
    # Cron endpoint for scheduled sync (used by Render Cron Jobs)
    path("api/cron/sync/", sync_views.CronSyncAPIView.as_view(), name="cron-sync"),
    # Add sync status endpoint at both /api/sync/ and /api/v1/sync/
    path("api/v1/sync/", include("apps.sync.urls")),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
