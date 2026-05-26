"""Validation helpers for user backup v1 bundles."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

BACKUP_FORMAT_VERSION = 1
BACKUP_APP_NAME = "richtato"

REQUIRED_TOP_LEVEL_KEYS = (
    "format_version",
    "exported_at",
    "app",
    "profile",
    "preferences",
    "categories",
    "budgets",
    "accounts",
    "transactions",
)


def parse_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a date string (YYYY-MM-DD)")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid date (YYYY-MM-DD)") from exc


def parse_decimal(value: Any, field_name: str) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid decimal") from exc


def validate_bundle_structure(bundle: dict[str, Any]) -> list[str]:
    """Return a list of validation errors; empty list means structurally valid."""
    errors: list[str] = []

    if not isinstance(bundle, dict):
        return ["Backup must be a JSON object"]

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in bundle:
            errors.append(f"Missing required field: {key}")

    if errors:
        return errors

    if bundle.get("format_version") != BACKUP_FORMAT_VERSION:
        errors.append(f"Unsupported format_version: {bundle.get('format_version')}")

    if bundle.get("app") != BACKUP_APP_NAME:
        errors.append(f"Unsupported app: {bundle.get('app')}")

    for list_key in ("categories", "budgets", "accounts", "transactions"):
        if not isinstance(bundle.get(list_key), list):
            errors.append(f"{list_key} must be an array")

    profile = bundle.get("profile")
    if not isinstance(profile, dict):
        errors.append("profile must be an object")

    preferences = bundle.get("preferences")
    if not isinstance(preferences, dict):
        errors.append("preferences must be an object")

    return errors


def summarize_bundle(bundle: dict[str, Any]) -> dict[str, int]:
    return {
        "categories": len(bundle.get("categories") or []),
        "budgets": len(bundle.get("budgets") or []),
        "accounts": len(bundle.get("accounts") or []),
        "transactions": len(bundle.get("transactions") or []),
    }


def build_account_keys(accounts: list[dict[str, Any]]) -> tuple[set[str], list[str]]:
    """Validate account keys are unique; return keys and errors."""
    keys: set[str] = set()
    errors: list[str] = []
    for index, account in enumerate(accounts):
        key = account.get("key")
        if not isinstance(key, str) or not key.strip():
            errors.append(f"accounts[{index}] missing valid key")
            continue
        if key in keys:
            errors.append(f"Duplicate account key: {key}")
        keys.add(key)
    return keys, errors


def validate_references(bundle: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Validate cross-references within a bundle. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    categories = bundle.get("categories") or []
    accounts = bundle.get("accounts") or []
    transactions = bundle.get("transactions") or []
    budgets = bundle.get("budgets") or []

    category_slugs = {cat.get("slug") for cat in categories if isinstance(cat.get("slug"), str)}
    account_keys, account_errors = build_account_keys(accounts)
    errors.extend(account_errors)

    for index, cat in enumerate(categories):
        parent_slug = cat.get("parent_slug")
        slug = cat.get("slug")
        if parent_slug and parent_slug not in category_slugs:
            errors.append(f"categories[{index}] references unknown parent_slug: {parent_slug}")
        if parent_slug == slug:
            errors.append(f"categories[{index}] cannot be its own parent")

    for index, txn in enumerate(transactions):
        account_key = txn.get("account_key")
        if account_key not in account_keys:
            errors.append(f"transactions[{index}] references unknown account_key: {account_key}")
        category_slug = txn.get("category_slug")
        if category_slug and category_slug not in category_slugs:
            warnings.append(
                f"transactions[{index}] references unknown category_slug: {category_slug} (will use uncategorized)"
            )

    for b_index, budget in enumerate(budgets):
        for a_index, allocation in enumerate(budget.get("allocations") or []):
            category_slug = allocation.get("category_slug")
            if category_slug and category_slug not in category_slugs:
                errors.append(
                    f"budgets[{b_index}].allocations[{a_index}] references unknown category_slug: {category_slug}"
                )

    return errors, warnings


def exported_at_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
