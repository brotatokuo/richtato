# API-only views for richtato_user app
import json

import pytz
from apps.card.serializers import CardAccountSerializer
from apps.card.services.card_account_service import CardAccountService
from apps.category.models import Category
from apps.category.services.category_service import CategoryService
from apps.expense.models import Expense
from apps.income.models import Income
from apps.richtato_user.demo_user_factory import DemoUserFactory
from apps.richtato_user.models import UserPreference
from apps.richtato_user.serializers import CategorySerializer, UserPreferenceSerializer
from apps.richtato_user.services.graph_service import GraphService
from apps.richtato_user.services.user_service import UserService
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


# API Views
class CardBanksAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.card_account_service = CardAccountService()

    @swagger_auto_schema(
        operation_summary="Get user card accounts",
        operation_description="Retrieve all card accounts for the authenticated user",
        responses={
            200: openapi.Response(
                "Success", examples={"application/json": {"data": []}}
            )
        },
    )
    def get(self, request, **kwargs):
        pk = kwargs.get("pk")
        if pk is not None:
            card_data = self.card_account_service.get_card_account_by_id(
                pk, request.user
            )
            if not card_data:
                return Response(
                    {"error": "Card account not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(card_data)

        data = self.card_account_service.get_user_card_accounts_formatted(request.user)
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Create a new card account",
        operation_description="Create a new card account for the authenticated user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING),
                "bank": openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=["name", "bank"],
        ),
        responses={
            201: openapi.Response("Card account created successfully"),
            400: openapi.Response("Invalid input data"),
        },
    )
    def post(self, request):
        serializer = CardAccountSerializer(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data["name"]
            bank = serializer.validated_data["bank"]
            card_data = self.card_account_service.create_card_account(
                request.user, name, bank
            )
            logger.debug(f"Created card account: {card_data}")
            return Response(card_data, status=status.HTTP_201_CREATED)
        logger.error(f"Error creating card account: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update a card account",
        operation_description="Update an existing card account for the authenticated user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING),
                "bank": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response("Card account updated successfully"),
            400: openapi.Response("Invalid input data"),
            404: openapi.Response("Card account not found"),
        },
    )
    def patch(self, request, **kwargs):
        pk = kwargs.get("pk")
        serializer = CardAccountSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            try:
                card_data = self.card_account_service.update_card_account(
                    pk, request.user, **serializer.validated_data
                )
                logger.debug(f"Updated card account {pk}: {card_data}")
                return Response(card_data)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        logger.error(f"Error updating card account {pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete a card account",
        operation_description="Delete a card account for the authenticated user",
        responses={
            204: openapi.Response("Card account deleted successfully"),
            404: openapi.Response("Card account not found"),
        },
    )
    def delete(self, request, **kwargs):
        pk = kwargs.get("pk")
        try:
            self.card_account_service.delete_card_account(pk, request.user)
            logger.debug(f"Deleted card account {pk}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class CombinedGraphAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.graph_service = GraphService()

    @swagger_auto_schema(
        operation_summary="Get combined income/expense graph data",
        operation_description="Retrieve chart data for income and expenses by month",
        responses={
            200: openapi.Response(
                "Success", examples={"application/json": {"labels": [], "datasets": []}}
            )
        },
    )
    def get(self, request):
        chart_data = self.graph_service.get_combined_graph_data(
            request.user, Expense, Income
        )
        logger.debug(f"Combined chart data: {chart_data}")
        return Response(chart_data)


class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_service = CategoryService()

    @swagger_auto_schema(
        operation_summary="Get user categories",
        operation_description="Retrieve all categories that have been used in transactions",
        responses={
            200: openapi.Response(
                "Success", examples={"application/json": {"columns": [], "rows": []}}
            )
        },
    )
    def get(self, request) -> Response:
        # Return enabled categories for the user in a simple list format
        results = self.category_service.get_enabled_categories(request.user)
        return Response({"results": results})

    @swagger_auto_schema(
        operation_summary="Create new category",
        operation_description="Create a new category for the authenticated user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Category name"
                ),
                "type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Category type"
                ),
            },
            required=["name", "type"],
        ),
        responses={
            201: openapi.Response("Created"),
            400: openapi.Response("Bad Request"),
        },
    )
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data["name"]
            category_type = serializer.validated_data["type"]
            enabled = serializer.validated_data.get("enabled", True)
            category_data = self.category_service.create_category(
                request.user, name, category_type, enabled
            )
            return Response(category_data, status=201)
        else:
            return Response(serializer.errors, status=400)

    @swagger_auto_schema(
        operation_summary="Update category",
        operation_description="Update an existing category",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Category name"
                ),
                "type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Category type"
                ),
            },
        ),
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request"),
            404: openapi.Response("Not Found"),
        },
    )
    def put(self, request, pk):
        serializer = CategorySerializer(data=request.data, partial=True)
        if serializer.is_valid():
            try:
                category_data = self.category_service.update_category(
                    pk, request.user, **serializer.validated_data
                )
                return Response(category_data)
            except ValueError as e:
                return Response({"error": str(e)}, status=404)
        return Response(serializer.errors, status=400)

    @swagger_auto_schema(
        operation_summary="Delete category",
        operation_description="Delete a category",
        responses={
            204: openapi.Response("No Content"),
            404: openapi.Response("Not Found"),
        },
    )
    def delete(self, request, pk):
        try:
            self.category_service.delete_category(pk, request.user)
            return Response(status=204)
        except ValueError as e:
            return Response({"error": str(e)}, status=404)


class CategoryFieldChoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_service = CategoryService()

    @swagger_auto_schema(
        operation_summary="Get category field choices",
        operation_description="Get available choices for category fields",
        responses={
            200: openapi.Response(
                "Success", examples={"application/json": {"type_choices": []}}
            )
        },
    )
    def get(self, request):
        choices = self.category_service.get_field_choices()
        return Response({"type_choices": choices["type"]})


class CategorySettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_service = CategoryService()

    @swagger_auto_schema(
        operation_summary="Get full category catalog with enabled flags",
        responses={200: openapi.Response("Success")},
    )
    def get(self, request):
        registry = BaseCategory.get_registry()
        user_cats = {c.name: c for c in Category.objects.filter(user=request.user)}
        # Gather existing budgets keyed by category name
        from apps.budget.models import Budget

        cat_to_budget = {
            b.category.name: b
            for b in Budget.objects.filter(user=request.user).select_related("category")
        }
        catalog = []
        for display_name, cls in registry.items():
            normalized = display_name.replace("/", "_")
            instance = cls()
            existing = user_cats.get(normalized)
            budget = cat_to_budget.get(normalized)
            catalog.append(
                {
                    "name": normalized,
                    "display": display_name,
                    "icon": instance.icon,
                    "color": instance.color,
                    "type": existing.type if existing else None,
                    "enabled": existing.enabled if existing else False,
                    "budget": (
                        {
                            "id": budget.id,
                            "amount": float(budget.amount),
                            "start_date": budget.start_date.isoformat(),
                            "end_date": budget.end_date.isoformat()
                            if budget.end_date
                            else None,
                        }
                        if budget
                        else None
                    ),
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
        enabled = set(request.data.get("enabled", []))
        disabled = set(request.data.get("disabled", []))
        budgets = request.data.get(
            "budgets", {}
        )  # name -> { amount, start_date?, end_date? | null }

        # Enforce Unknown stays enabled
        enabled.add("Unknown")

        valid_names = {k.replace("/", "_") for k in BaseCategory.get_registry().keys()}
        bad = (enabled | disabled) - valid_names
        if bad:
            return Response({"error": f"Unknown categories: {sorted(bad)}"}, status=400)

        # Ensure Category rows exist for enabled names
        existing = {
            c.name: c
            for c in Category.objects.filter(
                user=request.user, name__in=list(enabled | disabled)
            )
        }
        to_create = []
        for name in enabled:
            if name not in existing:
                # Default type: essential unless listed as nonessential in defaults
                # We can reuse create_default_categories_for_user mapping quickly:
                # Fall back to essential if unknown
                default_type = "essential"
                to_create.append(
                    Category(
                        user=request.user, name=name, type=default_type, enabled=True
                    )
                )
        if to_create:
            Category.objects.bulk_create(to_create)

        Category.objects.filter(user=request.user, name__in=list(enabled)).update(
            enabled=True
        )
        Category.objects.filter(user=request.user, name__in=list(disabled)).update(
            enabled=False
        )

        # Handle budgets: create/update/delete as needed
        from decimal import Decimal

        from apps.budget.models import Budget

        cat_map = {
            c.name: c
            for c in Category.objects.filter(user=request.user, name__in=budgets.keys())
        }
        existing_budgets = {
            b.category.name: b
            for b in Budget.objects.filter(user=request.user).select_related("category")
        }

        for name, bdata in budgets.items():
            if bdata is None:
                # Delete existing budget if present
                if name in existing_budgets:
                    existing_budgets[name].delete()
            else:
                # Create or update budget
                amount = bdata.get("amount")
                start_date_str = bdata.get("start_date")
                end_date_str = bdata.get("end_date")
                if amount is None:
                    continue
                amount = Decimal(str(amount))

                # Parse dates
                import datetime

                start_date = (
                    datetime.date.fromisoformat(start_date_str)
                    if start_date_str
                    else datetime.date.today()
                )
                end_date = (
                    datetime.date.fromisoformat(end_date_str) if end_date_str else None
                )

                cat = cat_map.get(name)
                if not cat:
                    # If category doesn't exist yet, skip
                    continue

                if name in existing_budgets:
                    # Update existing budget
                    b = existing_budgets[name]
                    b.amount = amount
                    b.start_date = start_date
                    b.end_date = end_date
                    b.save()
                else:
                    # Create new budget
                    Budget.objects.create(
                        user=request.user,
                        category=cat,
                        amount=amount,
                        start_date=start_date,
                        end_date=end_date,
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
