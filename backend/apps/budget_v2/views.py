"""Views for budget v2 API."""

from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.budget_v2.serializers import (
    BudgetCreateSerializer,
    BudgetSerializer,
)
from apps.budget_v2.services.budget_calculation_service import BudgetCalculationService
from apps.budget_v2.services.budget_service import BudgetService
from loguru import logger


class BudgetListCreateAPIView(APIView):
    """List all budgets or create a new one."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.budget_service = BudgetService()

    def get(self, request):
        """List all budgets for the user."""
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        budgets = self.budget_service.get_user_budgets(request.user, active_only)
        serializer = BudgetSerializer(budgets, many=True)
        return Response({"budgets": serializer.data})

    def post(self, request):
        """Create a new budget."""
        serializer = BudgetCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            budget = self.budget_service.create_budget(
                user=request.user, **serializer.validated_data
            )

            response_serializer = BudgetSerializer(budget)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating budget: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BudgetDetailAPIView(APIView):
    """Retrieve, update or delete a budget."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.budget_service = BudgetService()

    def get(self, request, pk):
        """Get budget details."""
        budget = self.budget_service.get_budget_by_id(pk, request.user)

        if not budget:
            return Response(
                {"error": "Budget not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = BudgetSerializer(budget)
        return Response(serializer.data)

    def delete(self, request, pk):
        """Delete (deactivate) budget."""
        budget = self.budget_service.get_budget_by_id(pk, request.user)

        if not budget:
            return Response(
                {"error": "Budget not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            self.budget_service.delete_budget(budget)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error deleting budget {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BudgetProgressAPIView(APIView):
    """Get budget progress with transaction data."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.budget_service = BudgetService()
        self.calculation_service = BudgetCalculationService()

    def get(self, request, pk):
        """Get detailed budget progress."""
        budget = self.budget_service.get_budget_by_id(pk, request.user)

        if not budget:
            return Response(
                {"error": "Budget not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            progress = self.calculation_service.calculate_budget_progress(budget)
            return Response(progress)

        except Exception as e:
            logger.error(f"Error calculating budget progress for {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CurrentBudgetAPIView(APIView):
    """Get the currently active budget with progress."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.budget_service = BudgetService()
        self.calculation_service = BudgetCalculationService()

    def get(self, request):
        """Get current budget."""
        budget = self.budget_service.get_current_budget(request.user)

        if not budget:
            return Response(
                {"error": "No active budget found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Get budget data
            serializer = BudgetSerializer(budget)
            budget_data = serializer.data

            # Get progress
            progress = self.calculation_service.calculate_budget_progress(budget)

            return Response({"budget": budget_data, "progress": progress})

        except Exception as e:
            logger.error(f"Error getting current budget: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
