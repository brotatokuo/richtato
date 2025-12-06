# API-only views for richtato_user app
import json
from decimal import Decimal

import pytz
from apps.richtato_user.demo_user_factory import DemoUserFactory
from apps.richtato_user.models import UserPreference
from apps.richtato_user.serializers import UserPreferenceSerializer
from apps.richtato_user.services.user_service import UserService
from apps.transaction.models import Transaction, TransactionCategory
from apps.budget.models import Budget, BudgetCategory
from categories.categories import BaseCategory
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from loguru import logger
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

pst = pytz.timezone("US/Pacific")


class CategorySettingsAPIView(APIView):
    """API view for managing transaction categories and budgets."""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get full category catalog with enabled flags",
        responses={200: openapi.Response("Success")},
    )
    def get(self, request):
        """Get all available categories with their settings."""
        registry = BaseCategory.get_registry()
        user_cats = {
            c.slug: c for c in TransactionCategory.objects.filter(user=request.user)
        }

        # Get current active budgets
        cat_to_budget = {}
        active_budgets = Budget.objects.filter(
            user=request.user, is_active=True
        ).prefetch_related("budget_categories__category")
        for budget in active_budgets:
            for bc in budget.budget_categories.all():
                cat_to_budget[bc.category.slug] = {
                    "id": bc.id,
                    "amount": float(bc.allocated_amount),
                    "start_date": budget.start_date.isoformat(),
                    "end_date": budget.end_date.isoformat()
                    if budget.end_date
                    else None,
                }

        catalog = []
        for display_name, cls in registry.items():
            slug = display_name.lower().replace("/", "-").replace(" ", "-")
            instance = cls()
            existing = user_cats.get(slug)
            budget_info = cat_to_budget.get(slug)
            catalog.append(
                {
                    "name": slug,
                    "display": display_name,
                    "icon": instance.icon,
                    "color": instance.color,
                    "is_expense": existing.is_expense if existing else True,
                    "is_income": existing.is_income if existing else False,
                    "enabled": existing is not None,
                    "budget": budget_info,
                }
            )
        return Response({"categories": catalog})

    @swagger_auto_schema(
        operation_summary="Bulk enable/disable categories",
        operation_description="Body: { enabled: string[], disabled: string[] }",
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request"),
        },
    )
    def put(self, request):
        """Update category settings, budgets, and category types."""
        enabled = set(request.data.get("enabled", []))
        disabled = set(request.data.get("disabled", []))
        budgets = request.data.get("budgets", {})
        category_types = request.data.get("category_types", {})

        # Create categories that don't exist
        existing = {
            c.slug: c for c in TransactionCategory.objects.filter(user=request.user)
        }

        to_create = []
        for slug in enabled:
            if slug not in existing:
                # Check if we have type info for this new category
                cat_type = category_types.get(slug, "expense")
                is_income = cat_type == "income"
                is_expense = cat_type == "expense"
                to_create.append(
                    TransactionCategory(
                        user=request.user,
                        name=slug.replace("-", " ").replace("_", " ").title(),
                        slug=slug,
                        is_income=is_income,
                        is_expense=is_expense,
                    )
                )
        if to_create:
            TransactionCategory.objects.bulk_create(to_create)

        # Update category types for existing categories
        if category_types:
            for slug, cat_type in category_types.items():
                if slug in existing:
                    cat = existing[slug]
                    cat.is_income = cat_type == "income"
                    cat.is_expense = cat_type == "expense"
                    cat.save(update_fields=["is_income", "is_expense"])

        # Delete disabled categories (or just remove from user's list)
        TransactionCategory.objects.filter(
            user=request.user, slug__in=list(disabled)
        ).delete()

        # Handle budgets
        if budgets:
            # Get or create a monthly budget for the user
            from datetime import date, timedelta

            today = date.today()
            start_date = today.replace(day=1)
            if start_date.month == 12:
                end_date = start_date.replace(
                    year=start_date.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                end_date = start_date.replace(
                    month=start_date.month + 1, day=1
                ) - timedelta(days=1)

            budget, _ = Budget.objects.get_or_create(
                user=request.user,
                start_date=start_date,
                end_date=end_date,
                defaults={
                    "name": f"Monthly Budget - {start_date.strftime('%B %Y')}",
                    "period_type": "monthly",
                    "is_active": True,
                },
            )

            cat_map = {
                c.slug: c
                for c in TransactionCategory.objects.filter(
                    user=request.user, slug__in=budgets.keys()
                )
            }

            existing_bc = {
                bc.category.slug: bc
                for bc in BudgetCategory.objects.filter(budget=budget)
            }

            for slug, bdata in budgets.items():
                if bdata is None:
                    # Delete existing budget category if present
                    if slug in existing_bc:
                        existing_bc[slug].delete()
                else:
                    amount = bdata.get("amount")
                    if amount is None:
                        continue

                    cat = cat_map.get(slug)
                    if not cat:
                        continue

                    if slug in existing_bc:
                        bc = existing_bc[slug]
                        bc.allocated_amount = Decimal(str(amount))
                        bc.save()
                    else:
                        BudgetCategory.objects.create(
                            budget=budget,
                            category=cat,
                            allocated_amount=Decimal(str(amount)),
                        )

        return Response({"message": "Category settings updated"})


class UserPreferenceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get user preferences",
        operation_description="Retrieve preferences for the authenticated user",
        responses={
            200: openapi.Response(
                "Success",
                examples={"application/json": {"theme": "light", "currency": "USD"}},
            )
        },
    )
    def get(self, request):
        try:
            preferences = UserPreference.objects.get(user=request.user)
            serializer = UserPreferenceSerializer(preferences)
            return Response(serializer.data)
        except UserPreference.DoesNotExist:
            # Return default preferences
            return Response(
                {"theme": "system", "currency": "USD", "date_format": "MM/DD/YYYY"}
            )

    @swagger_auto_schema(
        operation_summary="Update user preferences",
        operation_description="Update preferences for the authenticated user",
        request_body=UserPreferenceSerializer,
        responses={
            200: openapi.Response("Preferences updated successfully"),
            400: openapi.Response("Invalid input data"),
        },
    )
    def put(self, request):
        try:
            preferences = UserPreference.objects.get(user=request.user)
            serializer = UserPreferenceSerializer(
                preferences, data=request.data, partial=True
            )
        except UserPreference.DoesNotExist:
            serializer = UserPreferenceSerializer(data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class UserPreferenceFieldChoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get user preference field choices",
        operation_description="Get available choices for user preference fields",
        responses={
            200: openapi.Response(
                "Success",
                examples={
                    "application/json": {
                        "theme": [],
                        "date_format": [],
                        "currency": [],
                        "timezone": [],
                    }
                },
            )
        },
    )
    def get(self, request):
        return Response(
            {
                "theme": [
                    {"value": val, "label": label}
                    for val, label in UserPreference.THEME_CHOICES
                ],
                "date_format": [
                    {"value": val, "label": label}
                    for val, label in UserPreference.DATE_FORMAT_CHOICES
                ],
                "currency": [
                    {"value": val, "label": label}
                    for val, label in UserPreference.CURRENCY_CHOICES
                ],
                "timezone": [
                    {"value": val, "label": label}
                    for val, label in UserPreference.TIMEZONE_CHOICES
                ],
            }
        )


# Django views (CSRF-based authentication)
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


class LoginView(APIView):
    permission_classes = []  # Allow unauthenticated access
    authentication_classes = []  # Disable authentication but keep CSRF via middleware

    @swagger_auto_schema(
        operation_summary="Login",
        operation_description="Authenticate a user and start a session",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(type=openapi.TYPE_STRING),
                "password": openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=["username", "password"],
        ),
        responses={
            200: openapi.Response("Login successful"),
            401: openapi.Response("Invalid credentials"),
        },
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user_service = UserService()
        user = user_service.authenticate_user(username, password)

        if user:
            login(request, user)
            return JsonResponse(
                {"message": "Login successful", "user_id": user.id}, status=200
            )
        return JsonResponse({"error": "Invalid credentials"}, status=401)


class RegisterView(APIView):
    permission_classes = []  # Allow unauthenticated access
    authentication_classes = []  # Disable authentication but keep CSRF via middleware

    @swagger_auto_schema(
        operation_summary="Register",
        operation_description="Register a new user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(type=openapi.TYPE_STRING),
                "password": openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=["username", "password"],
        ),
        responses={
            201: openapi.Response("Registration successful"),
            400: openapi.Response("Username already exists or invalid input"),
        },
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return JsonResponse(
                {"error": "Username and password are required"}, status=400
            )

        user_service = UserService()

        if not user_service.check_username_availability(username):
            return JsonResponse({"error": "Username already exists"}, status=400)

        try:
            user = user_service.create_user(username, password)
            login(request, user)
            return JsonResponse(
                {"message": "Registration successful", "user_id": user.id}, status=201
            )
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return JsonResponse({"error": str(e)}, status=500)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Logout",
        operation_description="End the user session",
        responses={
            200: openapi.Response("Logout successful"),
        },
    )
    def post(self, request):
        logout(request)
        return JsonResponse({"message": "Logged out successfully"}, status=200)


@login_required
@require_http_methods(["GET"])
def get_user_id(request: HttpRequest):
    """
    Get the user ID of the currently logged-in user.
    Useful for frontend to verify session state.
    """
    return JsonResponse({"user_id": request.user.id})


@login_required
@require_http_methods(["POST"])
def check_username_availability(request):
    """
    Check if a username is available.
    Request body: {"username": "someusername"}
    """
    try:
        data = json.loads(request.body)
        username = data.get("username")
        if not username:
            return JsonResponse({"error": "Username is required"}, status=400)

        user_service = UserService()
        available = user_service.check_username_availability(username)
        return JsonResponse({"available": available})
    except Exception as e:
        logger.error(f"Error checking username availability: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_username(request):
    """
    Update the current user's username.
    Request body: {"new_username": "newusername"}
    """
    try:
        data = json.loads(request.body)
        new_username = data.get("new_username")
        if not new_username:
            return JsonResponse({"error": "New username is required"}, status=400)

        user_service = UserService()
        try:
            user_service.update_username(request.user, new_username)
            return JsonResponse(
                {"message": "Username updated successfully", "username": new_username}
            )
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

    except Exception as e:
        logger.error(f"Error updating username: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def change_password(request):
    """
    Change the current user's password.
    Request body: {"current_password": "...", "new_password": "..."}
    """
    try:
        data = json.loads(request.body)
        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if not current_password or not new_password:
            return JsonResponse(
                {"error": "Both current and new password are required"}, status=400
            )

        # Verify current password
        user_service = UserService()
        user = user_service.authenticate_user(request.user.username, current_password)
        if not user:
            return JsonResponse({"error": "Current password is incorrect"}, status=400)

        # Update password
        user_service.update_password(request.user, new_password)
        return JsonResponse({"message": "Password changed successfully"})

    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_preferences(request):
    """
    Update user preferences (theme, currency, etc.)
    """
    try:
        data = json.loads(request.body)
        preferences, created = UserPreference.objects.get_or_create(user=request.user)

        if "theme" in data:
            preferences.theme = data["theme"]
        if "currency" in data:
            preferences.currency = data["currency"]
        if "date_format" in data:
            preferences.date_format = data["date_format"]

        preferences.save()
        return JsonResponse({"message": "Preferences updated successfully"})

    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_account(request):
    """Delete the current user's account."""
    try:
        user_service = UserService()
        user_service.delete_user(request.user)
        logout(request)
        return JsonResponse({"message": "Account deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
def demo_login(request):
    """Create or login as a demo user."""
    try:
        demo_user = DemoUserFactory().create_or_reset()
        user_service = UserService()
        login(request, demo_user)
        profile_data = user_service.get_user_profile_data(demo_user)
        return Response(profile_data)
    except Exception as e:
        logger.error(f"Error creating demo user: {e}")
        return Response({"success": False, "error": str(e)}, status=500)


# API Authentication Views
class APILoginView(APIView):
    permission_classes = []  # Allow unauthenticated access
    authentication_classes = []  # Disable authentication but keep CSRF via middleware

    @swagger_auto_schema(
        operation_summary="API Login",
        operation_description="Authenticate a user via API",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(type=openapi.TYPE_STRING),
                "password": openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=["username", "password"],
        ),
        responses={
            200: openapi.Response("Login successful"),
            400: openapi.Response("Missing credentials"),
            401: openapi.Response("Invalid credentials"),
        },
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_service = UserService()
        user = user_service.authenticate_user(username, password)

        if user:
            login(request, user)
            profile_data = user_service.get_user_profile_data(user)
            return Response(
                {
                    "success": True,
                    "message": "Login successful",
                    "user": profile_data,
                    "token": "session-based",  # Using session authentication
                },
                status=200,
            )

        return Response(
            {"success": False, "error": "Invalid username or password"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class APILogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="API Logout",
        operation_description="End the user session via API",
        responses={200: openapi.Response("Logout successful")},
    )
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"}, status=200)


class APIProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_service = UserService()

    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description="Retrieve the authenticated user's profile",
        responses={200: openapi.Response("Profile data")},
    )
    def get(self, request):
        profile_data = self.user_service.get_user_profile_data(request.user)
        return Response(profile_data)


class APIDemoLoginView(APIView):
    permission_classes = []  # Allow unauthenticated access
    authentication_classes = []  # Disable authentication but keep CSRF via middleware

    @swagger_auto_schema(
        operation_summary="Demo Login",
        operation_description="Create and login as a demo user",
        responses={
            200: openapi.Response("Demo user created and logged in"),
            500: openapi.Response("Error creating demo user"),
        },
    )
    def post(self, request):

        try:
            demo_user = DemoUserFactory().create_or_reset()
            login(request, demo_user)
            user_service = UserService()
            profile_data = user_service.get_user_profile_data(demo_user)
            return Response(
                {
                    "success": True,
                    "message": "Demo user created and logged in",
                    "user": profile_data,
                    "token": "session-based",  # Using session authentication
                }
            )
        except Exception as e:
            logger.error(f"Error creating demo user: {e}")
            return Response({"success": False, "error": str(e)}, status=500)


class CategoriesAPIView(APIView):
    """API view for listing transaction categories."""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get all transaction categories",
        responses={200: openapi.Response("Success")},
    )
    def get(self, request):
        """Get all transaction categories for the user."""
        categories = TransactionCategory.objects.filter(user=request.user)
        results = [
            {
                "id": cat.id,
                "name": cat.name,
                "type": "expense" if cat.is_expense else "income",
            }
            for cat in categories
        ]
        return Response({"results": results})
