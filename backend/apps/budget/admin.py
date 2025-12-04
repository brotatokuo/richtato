"""Admin configuration for budget v2."""

from django.contrib import admin

from .models import Budget, BudgetCategory, BudgetProgress


class BudgetCategoryInline(admin.TabularInline):
    model = BudgetCategory
    extra = 1


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "period_type",
        "start_date",
        "end_date",
        "is_active",
        "created_at",
    )
    list_filter = ("period_type", "is_active", "created_at")
    search_fields = ("name", "user__username")
    inlines = [BudgetCategoryInline]
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("user",)


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "budget",
        "category",
        "allocated_amount",
        "rollover_enabled",
        "rollover_amount",
    )
    list_filter = ("rollover_enabled", "created_at")
    search_fields = ("budget__name", "category__name")
    list_select_related = ("budget", "category")


@admin.register(BudgetProgress)
class BudgetProgressAdmin(admin.ModelAdmin):
    list_display = (
        "budget_category",
        "period_start",
        "period_end",
        "spent_amount",
        "remaining_amount",
        "percentage_used",
        "last_calculated",
    )
    list_filter = ("period_start", "last_calculated")
    search_fields = ("budget_category__budget__name", "budget_category__category__name")
    readonly_fields = ("last_calculated", "percentage_used", "is_over_budget")
    list_select_related = (
        "budget_category",
        "budget_category__budget",
        "budget_category__category",
    )
