"""Service for category settings management."""

from datetime import date, timedelta
from decimal import Decimal

from apps.budget.models import Budget, BudgetCategory
from apps.transaction.models import TransactionCategory
from apps.transaction.services.category_initialization_service import (
    CategoryInitializationService,
)
from django.utils.text import slugify


class CategorySettingsService:
    """Manages the category catalog, enable/disable, and budget allocation."""

    def __init__(self):
        self.init_service = CategoryInitializationService()

    def get_catalog(self, user) -> dict:
        config = self.init_service.load_defaults_config()

        user_cats = {
            c.slug: c
            for c in TransactionCategory.objects.filter(
                user=user
            ).prefetch_related("keywords")
        }

        cat_to_budget = {}
        active_budgets = Budget.objects.filter(
            user=user, is_active=True
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
        included_slugs = set()

        for cat_config in config.get("categories", []):
            name = cat_config.get("name", "")
            if not name:
                continue

            slug = slugify(name)
            included_slugs.add(slug)

            existing = user_cats.get(slug)
            budget_info = cat_to_budget.get(slug)
            cat_type = existing.type if existing else cat_config.get("type", "expense")

            keywords = []
            if existing:
                keywords = [
                    {
                        "id": kw.id,
                        "keyword": kw.keyword,
                        "match_count": kw.match_count,
                        "created_at": kw.created_at.isoformat(),
                    }
                    for kw in existing.keywords.all()
                ]

            catalog.append(
                {
                    "id": existing.id if existing else 0,
                    "name": slug,
                    "display": name,
                    "icon": cat_config.get("icon", ""),
                    "color": cat_config.get("color", ""),
                    "type": cat_type,
                    "expense_priority": existing.expense_priority if existing else None,
                    "is_essential": existing.expense_priority == "essential"
                    if existing
                    else False,
                    "enabled": existing is not None,
                    "budget": budget_info,
                    "keywords": keywords,
                }
            )

        for slug, cat in user_cats.items():
            if slug in included_slugs:
                continue
            if cat.is_deleted:
                continue

            budget_info = cat_to_budget.get(slug)
            keywords = [
                {
                    "id": kw.id,
                    "keyword": kw.keyword,
                    "match_count": kw.match_count,
                    "created_at": kw.created_at.isoformat(),
                }
                for kw in cat.keywords.all()
            ]

            catalog.append(
                {
                    "id": cat.id,
                    "name": slug,
                    "display": cat.name,
                    "icon": cat.icon or "📁",
                    "color": cat.color or "",
                    "type": cat.type,
                    "expense_priority": cat.expense_priority,
                    "is_essential": cat.expense_priority == "essential",
                    "enabled": True,
                    "budget": budget_info,
                    "keywords": keywords,
                }
            )

        return {"categories": catalog}

    def update_settings(self, user, data: dict) -> None:
        enabled = set(data.get("enabled", []))
        disabled = set(data.get("disabled", []))
        budgets = data.get("budgets", {})
        category_types = data.get("category_types", {})

        existing = {
            c.slug: c for c in TransactionCategory.objects.filter(user=user)
        }

        to_create = []
        for slug in enabled:
            if slug not in existing:
                cat_type = category_types.get(slug, "expense")
                to_create.append(
                    TransactionCategory(
                        user=user,
                        name=slug.replace("-", " ").replace("_", " ").title(),
                        slug=slug,
                        type=cat_type,
                    )
                )
        if to_create:
            TransactionCategory.objects.bulk_create(to_create)

        if category_types:
            for slug, cat_type in category_types.items():
                if slug in existing:
                    cat = existing[slug]
                    cat.type = cat_type
                    cat.save(update_fields=["type"])

        TransactionCategory.objects.filter(
            user=user, slug__in=list(disabled)
        ).delete()

        if budgets:
            self._sync_budgets(user, budgets)

    def _sync_budgets(self, user, budgets: dict) -> None:
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
            user=user,
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
                user=user, slug__in=budgets.keys()
            )
        }

        existing_bc = {
            bc.category.slug: bc
            for bc in BudgetCategory.objects.filter(budget=budget)
        }

        for slug, bdata in budgets.items():
            if bdata is None:
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
