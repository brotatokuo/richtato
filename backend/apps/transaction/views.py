"""Views for transactions API."""

from datetime import datetime

from apps.financial_account.services.account_service import AccountService
from apps.transaction.models import CategoryKeyword
from apps.transaction.repositories.category_repository import CategoryRepository
from apps.transaction.serializers import (
    CategoryCreateSerializer,
    CategoryKeywordCreateSerializer,
    CategoryKeywordSerializer,
    CategoryUpdateSerializer,
    TransactionCategorizeSerializer,
    TransactionCategorySerializer,
    TransactionCreateSerializer,
    TransactionSerializer,
    TransactionUpdateSerializer,
)
from apps.transaction.services.transaction_service import TransactionService
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class TransactionFilterOptionsAPIView(APIView):
    """Get distinct filter options for transactions (dates, categories, accounts, etc.)."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_service = TransactionService()
        self.account_service = AccountService()

    def get(self, request):
        """Return distinct values for filterable columns with counts."""
        from django.db.models import Count

        from apps.transaction.models import Transaction

        # Parse same filters as transaction list
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        account_id = request.query_params.get("account_id")
        category_id = request.query_params.get("category_id")
        transaction_type = request.query_params.get("type")

        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        account = None
        if account_id:
            account = self.account_service.get_account_by_id(
                int(account_id), request.user
            )
        category = None
        if category_id:
            category_repo = CategoryRepository()
            category = category_repo.get_by_id(int(category_id))

        base_qs = Transaction.objects.filter(user=request.user).select_related(
            "account", "category"
        )
        if start_date:
            base_qs = base_qs.filter(date__gte=start_date)
        if end_date:
            base_qs = base_qs.filter(date__lte=end_date)
        if account:
            base_qs = base_qs.filter(account=account)
        if category:
            base_qs = base_qs.filter(category=category)
        if transaction_type:
            base_qs = base_qs.filter(transaction_type=transaction_type)

        # Distinct dates with count
        date_options = list(
            base_qs.values("date")
            .annotate(count=Count("id"))
            .order_by("-date")
            .values_list("date", "count")
        )
        dates = [
            {"label": d.isoformat(), "value": d.isoformat(), "count": c}
            for d, c in date_options
        ]

        # Distinct category types (from category.type or 'uncategorized')
        from django.db.models import Case, F, Value, When

        type_agg = (
            base_qs.annotate(
                cat_type=Case(
                    When(category__isnull=True, then=Value("uncategorized")),
                    default=F("category__type"),
                )
            )
            .values("cat_type")
            .annotate(count=Count("id"))
        )
        category_types = [
            {
                "label": ct["cat_type"] or "uncategorized",
                "value": ct["cat_type"] or "uncategorized",
                "count": ct["count"],
            }
            for ct in type_agg
        ]

        # Distinct category names
        cat_agg = (
            base_qs.values("category__name")
            .annotate(count=Count("id"))
            .order_by("category__name")
        )
        categories = [
            {
                "label": c["category__name"] or "Uncategorized",
                "value": c["category__name"] or "Uncategorized",
                "count": c["count"],
            }
            for c in cat_agg
        ]

        # Distinct account names
        acc_agg = (
            base_qs.values("account__name")
            .annotate(count=Count("id"))
            .order_by("account__name")
        )
        accounts = [
            {
                "label": a["account__name"] or "Unknown",
                "value": a["account__name"] or "Unknown",
                "count": a["count"],
            }
            for a in acc_agg
        ]

        # Distinct amounts (as string for display)
        amount_agg = (
            base_qs.values("amount", "transaction_type")
            .annotate(count=Count("id"))
            .order_by("amount")
        )
        amounts = []
        for a in amount_agg:
            amt = a["amount"]
            signed = -float(amt) if a["transaction_type"] == "debit" else float(amt)
            val = str(signed)
            amounts.append({"label": val, "value": val, "count": a["count"]})

        # Distinct descriptions (limit to avoid huge response)
        desc_agg = (
            base_qs.values("description")
            .annotate(count=Count("id"))
            .order_by("-count")[:500]
        )
        descriptions = [
            {
                "label": d["description"] or "",
                "value": d["description"] or "",
                "count": d["count"],
            }
            for d in desc_agg
        ]

        return Response(
            {
                "dates": dates,
                "category_types": category_types,
                "categories": categories,
                "accounts": accounts,
                "amounts": amounts,
                "descriptions": descriptions,
            }
        )


class TransactionListCreateAPIView(APIView):
    """List all transactions or create a new manual transaction."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_service = TransactionService()
        self.account_service = AccountService()

    def get(self, request):
        """List transactions with optional filters and pagination."""
        # Parse filters
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        account_id = request.query_params.get("account_id")
        category_id = request.query_params.get("category_id")
        transaction_type = request.query_params.get("type")
        search = request.query_params.get("search")
        page = int(request.query_params.get("page", 1))
        page_size = min(
            int(request.query_params.get("page_size", 50)),
            100,
        )

        # Convert dates
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        # Get account and category if specified
        account = None
        if account_id:
            account = self.account_service.get_account_by_id(
                int(account_id), request.user
            )

        category = None
        if category_id:
            category_repo = CategoryRepository()
            category = category_repo.get_by_id(int(category_id))

        # Handle search (no pagination for search; returns limited results)
        if search:
            transactions = self.transaction_service.search_transactions(
                request.user, search
            )
            serializer = TransactionSerializer(transactions, many=True)
            return Response({"transactions": serializer.data})

        # Paginated list
        queryset = self.transaction_service.get_user_transactions(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            account=account,
            category=category,
            transaction_type=transaction_type,
        )
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        page_slice = queryset[start:end]
        serializer = TransactionSerializer(page_slice, many=True)

        return Response(
            {
                "transactions": serializer.data,
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "has_next": end < total_count,
            }
        )

    def post(self, request):
        """Create a new manual transaction."""
        serializer = TransactionCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get account
            account = self.account_service.get_account_by_id(
                serializer.validated_data["account_id"], request.user
            )
            if not account:
                return Response(
                    {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Create transaction
            transaction = self.transaction_service.create_manual_transaction(
                user=request.user,
                account=account,
                date=serializer.validated_data["date"],
                amount=serializer.validated_data["amount"],
                description=serializer.validated_data["description"],
                transaction_type=serializer.validated_data.get(
                    "transaction_type", "debit"
                ),
                category_id=serializer.validated_data.get("category_id"),
                status=serializer.validated_data.get("status", "posted"),
                notes=serializer.validated_data.get("notes", ""),
            )

            response_serializer = TransactionSerializer(transaction)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating manual transaction: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionDetailAPIView(APIView):
    """Retrieve, update or delete a transaction."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_service = TransactionService()

    def get(self, request, pk):
        """Get transaction details."""
        transaction = self.transaction_service.get_transaction_by_id(pk, request.user)

        if not transaction:
            return Response(
                {"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)

    def patch(self, request, pk):
        """Update transaction."""
        transaction = self.transaction_service.get_transaction_by_id(pk, request.user)

        if not transaction:
            return Response(
                {"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TransactionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated_transaction = self.transaction_service.update_transaction(
                transaction, **serializer.validated_data
            )
            response_serializer = TransactionSerializer(updated_transaction)
            return Response(response_serializer.data)

        except Exception as e:
            logger.error(f"Error updating transaction {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """Delete transaction."""
        transaction = self.transaction_service.get_transaction_by_id(pk, request.user)

        if not transaction:
            return Response(
                {"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            self.transaction_service.delete_transaction(transaction)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error deleting transaction {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionCategorizeAPIView(APIView):
    """Categorize a transaction."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_service = TransactionService()

    def post(self, request, pk):
        """Categorize a transaction."""
        transaction = self.transaction_service.get_transaction_by_id(pk, request.user)

        if not transaction:
            return Response(
                {"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TransactionCategorizeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated_transaction = self.transaction_service.categorize_transaction(
                transaction, serializer.validated_data["category_id"]
            )
            response_serializer = TransactionSerializer(updated_transaction)
            return Response(response_serializer.data)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error categorizing transaction {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionSummaryAPIView(APIView):
    """Get transaction summary for a date range."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_service = TransactionService()

    def get(self, request):
        """Get transaction summary."""
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        if not start_date_str or not end_date_str:
            return Response(
                {"error": "start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            summary = self.transaction_service.get_transaction_summary(
                request.user, start_date, end_date
            )
            return Response(summary)

        except ValueError as e:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error getting transaction summary: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionCashflowSummaryAPIView(APIView):
    """Get cashflow summary (income/expense/investment by category) for a date range."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_service = TransactionService()

    def get(self, request):
        """Get cashflow summary."""
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        if not start_date_str or not end_date_str:
            return Response(
                {"error": "start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            summary = self.transaction_service.get_cashflow_summary(
                request.user, start_date, end_date
            )
            return Response(summary)

        except ValueError as e:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error getting cashflow summary: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryListCreateAPIView(APIView):
    """List all categories or create a custom category."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_repository = CategoryRepository()

    def get(self, request):
        """List all categories for the user."""
        categories = self.category_repository.get_all_for_user(request.user)
        serializer = TransactionCategorySerializer(categories, many=True)
        return Response({"categories": serializer.data})

    def post(self, request):
        """Create a custom category."""
        serializer = CategoryCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            parent = None
            if serializer.validated_data.get("parent_id"):
                parent = self.category_repository.get_by_id(
                    serializer.validated_data["parent_id"]
                )

            # Auto-generate slug from name if not provided
            name = serializer.validated_data["name"]
            slug = serializer.validated_data.get("slug")
            if not slug:
                from django.utils.text import slugify

                slug = slugify(name)

            category = self.category_repository.create_category(
                name=name,
                slug=slug,
                user=request.user,
                parent=parent,
                icon=serializer.validated_data.get("icon", ""),
                color=serializer.validated_data.get("color", ""),
                category_type=serializer.validated_data.get("type", "expense"),
            )

            # Create keywords if provided
            keywords = serializer.validated_data.get("keywords", [])
            for keyword in keywords:
                CategoryKeyword.objects.create(
                    user=request.user,
                    category=category,
                    keyword=keyword.strip().lower(),
                )

            response_serializer = TransactionCategorySerializer(category)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating category: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryDetailAPIView(APIView):
    """Retrieve, update or delete a category."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_repository = CategoryRepository()

    def get(self, request, pk):
        """Get category details."""
        category = self.category_repository.get_by_id(pk)

        if not category or category.user != request.user:
            return Response(
                {"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TransactionCategorySerializer(category)
        return Response(serializer.data)

    def patch(self, request, pk):
        """Update category (including expense_priority)."""
        category = self.category_repository.get_by_id(pk)

        if not category or category.user != request.user:
            return Response(
                {"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategoryUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update fields
            for field, value in serializer.validated_data.items():
                setattr(category, field, value)
            category.save()

            response_serializer = TransactionCategorySerializer(category)
            return Response(response_serializer.data)

        except Exception as e:
            logger.error(f"Error updating category {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """Soft-delete a category (hides from UI but preserves transaction assignments)."""
        category = self.category_repository.get_by_id(pk)

        if not category or category.user != request.user:
            return Response(
                {"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Don't allow deleting uncategorized
        if category.slug == "uncategorized":
            return Response(
                {"error": "Cannot delete the Uncategorized category"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            self.category_repository.delete_category(category)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error deleting category {pk}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryKeywordAPIView(APIView):
    """Add, list, or remove keywords for a category."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_repository = CategoryRepository()

    def get(self, request, category_id):
        """Get all keywords for a category."""
        try:
            category = self.category_repository.get_by_id(category_id)
            if not category or (category.user and category.user != request.user):
                return Response(
                    {"error": "Category not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            keywords = CategoryKeyword.objects.filter(
                user=request.user, category=category
            ).order_by("-match_count", "keyword")

            serializer = CategoryKeywordSerializer(keywords, many=True)
            return Response({"keywords": serializer.data})

        except Exception as e:
            logger.error(f"Error getting keywords: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, category_id):
        """Add a keyword to a category."""
        serializer = CategoryKeywordCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get category and verify ownership
            category = self.category_repository.get_by_id(category_id)
            if not category or (category.user and category.user != request.user):
                return Response(
                    {"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Create keyword
            keyword_obj = CategoryKeyword.objects.create(
                user=request.user,
                category=category,
                keyword=serializer.validated_data["keyword"].strip().lower(),
            )

            response_serializer = CategoryKeywordSerializer(keyword_obj)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error adding keyword: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, category_id, keyword_id):
        """Remove a keyword from a category."""
        try:
            # Get category and verify ownership
            category = self.category_repository.get_by_id(category_id)
            if not category or (category.user and category.user != request.user):
                return Response(
                    {"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Delete keyword
            keyword_obj = CategoryKeyword.objects.filter(
                id=keyword_id, category=category
            ).first()

            if not keyword_obj:
                return Response(
                    {"error": "Keyword not found"}, status=status.HTTP_404_NOT_FOUND
                )

            keyword_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error removing keyword: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UncategorizedTransactionsAPIView(APIView):
    """Get uncategorized transactions."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_service = TransactionService()

    def get(self, request):
        """Get uncategorized transactions."""
        limit = int(request.query_params.get("limit", 100))

        try:
            transactions = self.transaction_service.get_uncategorized_transactions(
                request.user, limit=limit
            )
            serializer = TransactionSerializer(transactions, many=True)
            return Response({"transactions": serializer.data})

        except Exception as e:
            logger.error(f"Error getting uncategorized transactions: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecategorizeTransactionsAPIView(APIView):
    """API for bulk recategorization of transactions."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Start a bulk recategorization task."""
        import threading

        from apps.transaction.models import RecategorizationTask
        from apps.transaction.services.recategorization_service import (
            RecategorizationService,
        )

        keep_existing = request.data.get("keep_existing_for_unmatched", True)

        try:
            # Check if there's already an active task for this user
            active_task = RecategorizationTask.objects.filter(
                user=request.user, status__in=["pending", "processing"]
            ).first()

            if active_task:
                return Response(
                    {
                        "error": "A recategorization task is already in progress",
                        "task_id": active_task.id,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            # Create new task
            task = RecategorizationTask.objects.create(
                user=request.user, keep_existing_for_unmatched=keep_existing
            )

            # Start async processing in a background thread
            def process_recategorization():
                service = RecategorizationService()
                try:
                    service.recategorize_all_transactions(task)
                except Exception as e:
                    logger.error(f"Background recategorization failed: {str(e)}")

            thread = threading.Thread(target=process_recategorization)
            thread.daemon = True
            thread.start()

            return Response({"task_id": task.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error starting recategorization: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, task_id):
        """Get progress of a recategorization task."""
        from apps.transaction.models import RecategorizationTask

        try:
            task = RecategorizationTask.objects.get(id=task_id, user=request.user)

            progress_percent = 0
            if task.total_count > 0:
                progress_percent = (task.processed_count / task.total_count) * 100

            return Response(
                {
                    "status": task.status,
                    "total": task.total_count,
                    "processed": task.processed_count,
                    "updated": task.updated_count,
                    "progress_percent": round(progress_percent, 2),
                    "error": task.error_message if task.error_message else None,
                }
            )

        except RecategorizationTask.DoesNotExist:
            return Response(
                {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting recategorization progress: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
