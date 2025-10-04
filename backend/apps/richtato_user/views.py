# API-only views for richtato_user app
import json

import pytz
from apps.expense.models import Expense
from apps.income.models import Income
from apps.richtato_user.models import (
    CardAccount,
    Category,
    User,
)
from apps.richtato_user.serializers import CategorySerializer
from apps.richtato_user.utils import (
    _get_line_graph_data_by_month,
)
from categories.categories import BaseCategory
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from loguru import logger
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

pst = pytz.timezone("US/Pacific")


# API Views
class CardBanksAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get user card accounts",
        operation_description="Retrieve all card accounts for the authenticated user",
        responses={
            200: openapi.Response(
                "Success", examples={"application/json": {"data": []}}
            )
        },
    )
    def get(self, request):
        card_accounts = CardAccount.objects.filter(user=request.user)
        logger.debug(f"User card accounts: {card_accounts}")
        return Response(card_accounts)


class CombinedGraphAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
        expense_data = _get_line_graph_data_by_month(request.user, Expense)
        logger.debug(f"Expense data: {expense_data}")

        income_data = _get_line_graph_data_by_month(request.user, Income)
        logger.debug(f"Income data: {income_data}")

        chart_data = {
            "labels": expense_data["labels"],  # assumes income labels match
            "datasets": [
                {
                    "label": "Expenses",
                    "data": expense_data["values"],
                    "backgroundColor": "rgba(232, 82, 63, 0.2)",
                    "borderColor": "rgba(232, 82, 63, 0.5)",
                    "borderWidth": 1,
                    "fill": True,
                    "tension": 0.4,
                },
                {
                    "label": "Income",
                    "data": income_data["values"],
                    "backgroundColor": "rgba(152, 204, 44, 0.2)",
                    "borderColor": "rgba(152, 204, 44, 0.5)",
                    "borderWidth": 1,
                    "fill": True,
                    "tension": 0.4,
                },
            ],
        }

        logger.debug(f"Combined chart data: {chart_data}")
        return Response(chart_data)


class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

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
        # Only return categories that have been used in expenses (have transactions)
        categories = Category.objects.filter(
            user=request.user, transactions__isnull=False
        ).distinct()
        rows = []
        for category in categories:
            rows.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "type": category.get_type_display(),
                }
            )
        data = {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "name", "title": "Name"},
                {"field": "type", "title": "Type"},
            ],
            "rows": rows,
        }
        return Response(data)

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
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
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
        try:
            category = Category.objects.get(pk=pk, user=request.user)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)

        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
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
            category = Category.objects.get(pk=pk, user=request.user)
            category.delete()
            return Response(status=204)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)


class CategoryFieldChoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
        type_choices = [
            {"value": choice[0], "label": choice[1]}
            for choice in Category.CATEGORY_TYPES
        ]
        return Response({"type_choices": type_choices})


class CategorySettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get full category catalog with enabled flags",
        responses={200: openapi.Response("Success")},
    )
    def get(self, request):
        registry = BaseCategory.get_registry()
        user_cats = {c.name: c for c in Category.objects.filter(user=request.user)}
        catalog = []
        for display_name, cls in registry.items():
            normalized = display_name.replace("/", "_")
            instance = cls()
            existing = user_cats.get(normalized)
            catalog.append(
                {
                    "name": normalized,
                    "display": display_name,
                    "icon": instance.icon,
                    "color": instance.color,
                    "type": existing.type if existing else None,
                    "enabled": existing.enabled if existing else False,
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
        # Don't disable Unknown
        Category.objects.filter(
            user=request.user, name__in=list(disabled - {"Unknown"})
        ).update(enabled=False)

        return Response({"success": True})


# CSRF Token endpoint
@csrf_exempt
def get_csrf_token(request):
    """Get CSRF token for frontend"""
    token = get_token(request)
    return JsonResponse({"csrfToken": token})


# Authentication API Views
class LoginView(APIView):
    permission_classes = []  # Allow unauthenticated access for login

    @swagger_auto_schema(
        operation_summary="User login",
        operation_description="Authenticate user and return session information",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Password"
                ),
            },
            required=["username", "password"],
        ),
        responses={
            200: openapi.Response("Success"),
            401: openapi.Response("Unauthorized"),
        },
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response(
                {
                    "success": True,
                    "message": "Login successful",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "is_staff": user.is_staff,
                        "is_superuser": user.is_superuser,
                        "is_active": user.is_active,
                        "date_joined": user.date_joined,
                        "last_login": user.last_login,
                    },
                    "token": "session-based",  # Using session authentication
                }
            )
        else:
            return Response({"error": "Invalid credentials"}, status=401)


class RegisterView(APIView):
    permission_classes = []  # Allow unauthenticated access for registration

    @swagger_auto_schema(
        operation_summary="User registration",
        operation_description="Register a new user account",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Username"
                ),
                "email": openapi.Schema(type=openapi.TYPE_STRING, description="Email"),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Password"
                ),
                "password_confirm": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Password confirmation"
                ),
            },
            required=["username", "email", "password", "password_confirm"],
        ),
        responses={
            201: openapi.Response("Created"),
            400: openapi.Response("Bad Request"),
        },
    )
    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        password_confirm = request.data.get("password_confirm")

        if password != password_confirm:
            return Response({"error": "Passwords do not match"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=400)

        try:
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            return Response(
                {"message": "User created successfully", "user_id": user.id}, status=201
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="User logout",
        operation_description="Logout the authenticated user",
        responses={200: openapi.Response("Success")},
    )
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"})


# Additional API endpoints
@swagger_auto_schema(
    operation_summary="Get user ID",
    operation_description="Get the ID of the authenticated user",
    responses={
        200: openapi.Response("Success", examples={"application/json": {"userID": 1}})
    },
)
@login_required
def get_user_id(request: HttpRequest):
    return JsonResponse({"userID": request.user.pk})


@swagger_auto_schema(
    operation_summary="Check username availability",
    operation_description="Check if a username is available for registration",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "username": openapi.Schema(
                type=openapi.TYPE_STRING, description="Username to check"
            ),
        },
        required=["username"],
    ),
    responses={
        200: openapi.Response(
            "Success", examples={"application/json": {"available": True}}
        )
    },
)
@csrf_exempt
@require_http_methods(["POST"])
def check_username_availability(request):
    data = json.loads(request.body)
    username = data.get("username")

    if not username:
        return JsonResponse({"error": "Username is required"}, status=400)

    is_available = not User.objects.filter(username=username).exists()
    return JsonResponse({"available": is_available})


@swagger_auto_schema(
    operation_summary="Update username",
    operation_description="Update the username of the authenticated user",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "new_username": openapi.Schema(
                type=openapi.TYPE_STRING, description="New username"
            ),
        },
        required=["new_username"],
    ),
    responses={200: openapi.Response("Success"), 400: openapi.Response("Bad Request")},
)
@login_required
@require_http_methods(["POST"])
def update_username(request):
    data = json.loads(request.body)
    new_username = data.get("new_username")

    if not new_username:
        return JsonResponse({"error": "New username is required"}, status=400)

    if User.objects.filter(username=new_username).exists():
        return JsonResponse({"error": "Username already exists"}, status=400)

    request.user.username = new_username
    request.user.save()

    return JsonResponse({"message": "Username updated successfully"})


@swagger_auto_schema(
    operation_summary="Change password",
    operation_description="Change the password of the authenticated user",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "old_password": openapi.Schema(
                type=openapi.TYPE_STRING, description="Current password"
            ),
            "new_password": openapi.Schema(
                type=openapi.TYPE_STRING, description="New password"
            ),
        },
        required=["old_password", "new_password"],
    ),
    responses={200: openapi.Response("Success"), 400: openapi.Response("Bad Request")},
)
@login_required
@require_http_methods(["POST"])
def change_password(request):
    data = json.loads(request.body)
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return JsonResponse(
            {"error": "Both old and new passwords are required"}, status=400
        )

    if not request.user.check_password(old_password):
        return JsonResponse({"error": "Current password is incorrect"}, status=400)

    request.user.set_password(new_password)
    request.user.save()

    return JsonResponse({"message": "Password changed successfully"})


@swagger_auto_schema(
    operation_summary="Update user preferences",
    operation_description="Update user preferences and settings",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "preferences": openapi.Schema(
                type=openapi.TYPE_OBJECT, description="User preferences object"
            ),
        },
        required=["preferences"],
    ),
    responses={200: openapi.Response("Success"), 400: openapi.Response("Bad Request")},
)
@login_required
@require_http_methods(["POST"])
def update_preferences(request):
    data = json.loads(request.body)
    preferences = data.get("preferences", {})

    # Update user preferences here based on your User model
    # This is a placeholder implementation
    request.user.save()

    return JsonResponse({"message": "Preferences updated successfully"})


@swagger_auto_schema(
    operation_summary="Delete account",
    operation_description="Delete the authenticated user's account",
    responses={200: openapi.Response("Success"), 400: openapi.Response("Bad Request")},
)
@login_required
@require_http_methods(["POST"])
def delete_account(request):
    # Add confirmation logic here if needed
    request.user.delete()
    return JsonResponse({"message": "Account deleted successfully"})


# Demo login for development
@swagger_auto_schema(
    operation_summary="Demo login",
    operation_description="Login with demo user for development/testing",
    responses={200: openapi.Response("Success"), 400: openapi.Response("Bad Request")},
)
@csrf_exempt
def demo_login(request):
    """Demo login for development purposes"""
    try:
        # Create or get demo user
        demo_user, created = User.objects.get_or_create(
            username="demo_user",
            defaults={"email": "demo@richtato.local", "is_active": True},
        )

        if created:
            demo_user.set_password("demo_password")
            demo_user.save()

        # Login the demo user
        login(request, demo_user)

        return JsonResponse(
            {
                "message": "Demo login successful",
                "user_id": demo_user.id,
                "username": demo_user.username,
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# API Authentication endpoints
class APILoginView(APIView):
    permission_classes = []  # Allow unauthenticated access for API login

    @swagger_auto_schema(
        operation_summary="API Login",
        operation_description="Login via API and return authentication token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Password"
                ),
            },
            required=["username", "password"],
        ),
        responses={
            200: openapi.Response("Success"),
            401: openapi.Response("Unauthorized"),
        },
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Generate a token for the user
            from rest_framework.authtoken.models import Token

            token, created = Token.objects.get_or_create(user=user)

            login(request, user)

            # Prepare user data in the format expected by frontend
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email or "",
                "first_name": "",  # Custom User model doesn't have first_name
                "last_name": "",  # Custom User model doesn't have last_name
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "is_active": user.is_active,
                "date_joined": user.date_joined.isoformat()
                if user.date_joined
                else None,
                "last_login": None,  # Custom User model doesn't have last_login
            }

            return Response(
                {
                    "success": True,
                    "message": "Login successful",
                    "user": user_data,
                    "token": token.key,
                    "organization": None,  # TODO: Add organization support
                }
            )
        else:
            return Response({"error": "Invalid credentials"}, status=401)


class APILogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="API Logout",
        operation_description="Logout via API",
        responses={200: openapi.Response("Success")},
    )
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"})


class APIProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description="Get profile information for the authenticated user",
        responses={
            200: openapi.Response(
                "Success",
                examples={"application/json": {"user_id": 1, "username": "user"}},
            )
        },
    )
    def get(self, request):
        user = request.user

        # Prepare user data in the format expected by frontend
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email or "",
            "first_name": "",  # Custom User model doesn't have first_name
            "last_name": "",  # Custom User model doesn't have last_name
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "last_login": None,  # Custom User model doesn't have last_login
        }

        return Response(
            {
                "success": True,
                "user": user_data,
                "organization": None,  # TODO: Add organization support
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class APIDemoLoginView(APIView):
    permission_classes = []  # Allow unauthenticated access for demo login

    @swagger_auto_schema(
        operation_summary="API Demo Login",
        operation_description="Login with demo user via API",
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request"),
        },
    )
    def post(self, request):
        try:
            logger.info("Demo login request received")
            logger.info(f"Request method: {request.method}")
            logger.info(f"Request headers: {dict(request.headers)}")
            logger.info(f"Request user: {request.user}")
            logger.info(f"Request authenticated: {request.user.is_authenticated}")

            demo_user, created = User.objects.get_or_create(
                username="demo_user",
                defaults={"email": "demo@richtato.local", "is_active": True},
            )
            logger.info(f"Demo user created: {created}, user: {demo_user.username}")

            if created:
                demo_user.set_password("demo_password")
                demo_user.save()
                logger.info("Demo user password set")

            # Login the demo user
            login(request, demo_user)
            logger.info("Demo user logged in successfully")

            # Prepare user data in the format expected by frontend
            user_data = {
                "id": demo_user.id,
                "username": demo_user.username,
                "email": demo_user.email or "",
                "first_name": "",  # Custom User model doesn't have first_name
                "last_name": "",  # Custom User model doesn't have last_name
                "is_staff": demo_user.is_staff,
                "is_superuser": demo_user.is_superuser,
                "is_active": demo_user.is_active,
                "date_joined": demo_user.date_joined.isoformat()
                if demo_user.date_joined
                else None,
                "last_login": None,  # Custom User model doesn't have last_login
            }

            return Response(
                {
                    "success": True,
                    "message": "Demo login successful",
                    "user": user_data,
                    "token": "session-based",  # Using session authentication
                    "organization": None,  # Demo user doesn't have organization
                }
            )
        except Exception as e:
            logger.error(f"Demo login error: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({"success": False, "error": str(e)}, status=400)
