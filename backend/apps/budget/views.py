"""
Budget views - Thin HTTP wrappers delegating to service layer.

Following clean architecture: Views handle only HTTP concerns.
Business logic is in services, database access is in repositories.
"""

import calendar
from datetime import date, datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from loguru import logger
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from richtato.views import BaseAPIView

from .models import Budget
from .repositories import BudgetRepository, CategoryRepository, ExpenseRepository
from .serializers import BudgetSerializer
from .services import BudgetService


class BudgetAPIView(BaseAPIView):
    """ViewSet for managing budgets - THIN WRAPPER."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.budget_repo = BudgetRepository()
        self.expense_repo = ExpenseRepository()
        self.category_repo = CategoryRepository()
        # Inject service with dependencies
        self.budget_service = BudgetService(
            self.budget_repo, self.expense_repo, self.category_repo
        )

    @property
    def field_remap(self):
        return {}

    @swagger_auto_schema(
        operation_summary="Get budget entries",
        operation_description="Retrieve budget entries for the authenticated user or a specific budget by ID",
        manual_parameters=[
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Limit number of results",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: openapi.Response(
                "Success", examples={"application/json": {"columns": [], "rows": []}}
            ),
            404: openapi.Response("Not Found"),
        },
    )
    def get(self, request, pk=None):
        """Get budget entries - delegates to service layer."""
        if pk:
            # Get specific budget
            budget = get_object_or_404(Budget, pk=pk, user=request.user)
            serializer = BudgetSerializer(budget)
            return Response(serializer.data)

        # Get all budgets
        limit_param = request.GET.get("limit", None)
        try:
            limit = int(limit_param) if limit_param else None
        except ValueError:
            return Response({"error": "Invalid limit value"}, status=400)

        # Delegate to service
        data = self.budget_service.get_user_budgets_formatted(request.user, limit)
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Create budget entry",
        operation_description="Create a new budget entry for the authenticated user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "category": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Category ID"
                ),
                "amount": openapi.Schema(
                    type=openapi.TYPE_NUMBER, description="Budget amount"
                ),
                "start_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Start date",
                ),
                "end_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="End date (omit for no expiry)",
                ),
            },
            required=["category", "amount", "start_date"],
        ),
        responses={
            201: openapi.Response("Created"),
            400: openapi.Response("Bad Request"),
        },
    )
    def post(self, request):
        """Create a new budget - delegates to service layer."""
        modified_data = request.data.copy()
        modified_data["user"] = request.user.id
        if not modified_data.get("end_date"):
            modified_data["end_date"] = None
        logger.debug(f"POST data: {modified_data}")

        serializer = BudgetSerializer(data=modified_data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"POST error: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update budget entry",
        operation_description="Update an existing budget entry",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "category": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Category ID"
                ),
                "amount": openapi.Schema(
                    type=openapi.TYPE_NUMBER, description="Budget amount"
                ),
                "start_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Start date",
                ),
                "end_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="End date",
                ),
            },
        ),
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request"),
            404: openapi.Response("Not Found"),
        },
    )
    def patch(self, request, pk):
        """Update an existing budget - delegates to service layer."""
        logger.debug(f"PATCH data: {request.data}")
        reversed_data = self.apply_fieldmap(request.data)
        if "end_date" in reversed_data and not reversed_data.get("end_date"):
            reversed_data["end_date"] = None
        budget = get_object_or_404(Budget, pk=pk, user=request.user)

        serializer = BudgetSerializer(budget, data=reversed_data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        logger.error(f"PATCH error: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete budget entry",
        operation_description="Delete an existing budget entry",
        responses={
            204: openapi.Response("No Content"),
            404: openapi.Response("Not Found"),
        },
    )
    def delete(self, request, pk):
        """Delete an existing budget - delegates to service layer."""
        logger.debug(f"DELETE Budget ID: {pk}")
        budget = get_object_or_404(Budget, pk=pk, user=request.user)
        budget.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BudgetFieldChoicesView(APIView):
    """Get field choices for budget creation - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.budget_repo = BudgetRepository()
        self.expense_repo = ExpenseRepository()
        self.category_repo = CategoryRepository()
        # Inject service with dependencies
        self.budget_service = BudgetService(
            self.budget_repo, self.expense_repo, self.category_repo
        )

    @swagger_auto_schema(
        operation_summary="Get budget field choices",
        operation_description="Get available field choices for budget creation/editing",
        responses={
            200: openapi.Response(
                "Success", examples={"application/json": {"category": []}}
            )
        },
    )
    def get(self, request):
        """Get field choices - delegates to service layer."""
        data = self.budget_service.get_field_choices(request.user)
        return Response(data)
