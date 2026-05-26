"""Keyword-based transaction category matching."""

from __future__ import annotations

from apps.richtato_user.models import User
from apps.transaction.models import CategoryKeyword, TransactionCategory


def load_user_keywords(user: User) -> list[CategoryKeyword]:
    """Load all keyword rules for a user (call once per bulk job)."""
    return list(
        CategoryKeyword.objects.filter(user=user).select_related("category").order_by("-match_count", "keyword")
    )


def match_category_from_keywords(
    description: str | None,
    keywords: list[CategoryKeyword],
) -> TransactionCategory | None:
    """Match a description against preloaded keyword rules."""
    haystack = (description or "").lower()
    for keyword_obj in keywords:
        kw = keyword_obj.keyword.strip().lower()
        if kw and kw in haystack:
            return keyword_obj.category
    return None
