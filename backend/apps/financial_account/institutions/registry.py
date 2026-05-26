"""Single source of truth for supported institutions and statement parsers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from apps.financial_account.institutions.parsers.amex_checking_pdf import parse_amex_checking_pdf
from apps.financial_account.institutions.parsers.amex_xlsx import parse_amex_activity_excel
from apps.financial_account.institutions.parsers.robinhood_bank_pdf import parse_robinhood_bank_pdf
from apps.financial_account.institutions.parsers.robinhood_credit_pdf import parse_robinhood_credit_pdf

ACCOUNT_TYPE_LABELS: dict[str, str] = {
    "checking": "Checking Account",
    "savings": "Savings Account",
    "credit_card": "Credit Card",
    "investment": "Investment Account",
}

ALL_ACCOUNT_TYPES = tuple(ACCOUNT_TYPE_LABELS.keys())

_PARSER_CONFIGS: dict[str, dict[str, Any]] = {
    "bofa": {
        "display_name": "Bank of America",
        "date": ["Posted Date", "Transaction Date", "Date"],
        "description": ["Payee", "Description", "Description Original"],
        "amount": ["Amount"],
        "debit": ["Debit", "Withdrawal"],
        "credit": ["Credit", "Deposit"],
    },
    "marcus": {
        "display_name": "Marcus",
        "date": ["Date", "Transaction Date", "Post Date"],
        "description": ["Description", "Details", "Transaction"],
        "amount": ["Amount"],
        "debit": ["Debit", "Withdrawal"],
        "credit": ["Credit", "Deposit"],
    },
    "amex": {
        "display_name": "American Express",
        "date": ["Date", "Transaction Date"],
        "description": ["Description", "Appears On Your Statement As"],
        "amount": ["Amount"],
        "debit": ["Debit", "Charge"],
        "credit": ["Credit", "Payment"],
    },
    "amex_checking": {
        "display_name": "American Express Checking",
        "date": ["Date", "Transaction Date", "Posted Date"],
        "description": ["Description", "Memo", "Details"],
        "amount": ["Amount"],
        "debit": ["Debit", "Withdrawal"],
        "credit": ["Credit", "Deposit"],
    },
    "robinhood_bank": {
        "display_name": "Robinhood Bank",
        "date": ["Date", "Transaction Date", "Posted Date"],
        "description": ["Description", "Memo", "Details"],
        "amount": ["Amount"],
        "debit": ["Debit", "Withdrawal"],
        "credit": ["Credit", "Deposit"],
    },
    "fidelity": {
        "display_name": "Fidelity",
        "date": ["Run Date", "Date", "Settlement Date", "Trade Date"],
        "description": ["Description", "Action", "Name"],
        "amount": ["Amount", "Cash Amount", "Net Amount"],
        "debit": ["Debit"],
        "credit": ["Credit"],
        "activity": ["Action", "Activity Type", "Type"],
        "symbol": ["Symbol"],
        "quantity": ["Quantity", "Shares"],
    },
    "robinhood_investments": {
        "display_name": "Robinhood Investments",
        "date": ["Activity Date", "Date", "Trade Date"],
        "description": ["Description", "Instrument", "Trans Code"],
        "amount": ["Amount", "Value", "Net Amount"],
        "debit": ["Debit"],
        "credit": ["Credit"],
        "activity": ["Activity Type", "Trans Code", "Type"],
        "symbol": ["Symbol"],
        "quantity": ["Quantity"],
    },
    "guideline": {
        "display_name": "Guideline",
        "date": ["Date", "Transaction Date", "Payroll Date"],
        "description": ["Description", "Transaction Type", "Fund"],
        "amount": ["Amount", "Value"],
        "debit": ["Debit"],
        "credit": ["Credit", "Contribution"],
        "activity": ["Transaction Type", "Type", "Activity"],
        "symbol": ["Fund", "Symbol"],
        "quantity": ["Shares", "Units", "Quantity"],
    },
    "chase": {
        "display_name": "Chase",
        "date": ["Transaction Date", "Post Date", "Date"],
        "description": ["Description", "Payee"],
        "amount": ["Amount"],
        "debit": ["Debit", "Withdrawal"],
        "credit": ["Credit", "Deposit"],
    },
    "citi": {
        "display_name": "Citi",
        "date": ["Date", "Transaction Date"],
        "description": ["Description"],
        "amount": ["Amount"],
        "debit": ["Debit"],
        "credit": ["Credit"],
    },
    "robinhood_credit": {
        "display_name": "Robinhood Credit",
        "date": ["Post Date"],
        "description": ["Transaction Description"],
        "amount": ["Amount"],
    },
    "generic": {
        "display_name": "Generic CSV",
        "date": ["date"],
        "description": ["description"],
        "amount": ["amount"],
        "debit": [],
        "credit": [],
        "type": ["type", "transaction_type"],
    },
}

PARSER_READERS: dict[str, Callable[[bytes], pd.DataFrame]] = {
    "amex": parse_amex_activity_excel,
    "amex_checking": parse_amex_checking_pdf,
    "robinhood_bank": parse_robinhood_bank_pdf,
    "robinhood_credit": parse_robinhood_credit_pdf,
}

_DEFAULT_FILE_TYPES = ("csv", "xls", "xlsx")
_PDF_FILE_TYPES = ("pdf",)
_PARSER_FILE_TYPES: dict[str, tuple[str, ...]] = {
    "amex_checking": _PDF_FILE_TYPES,
    "robinhood_bank": _DEFAULT_FILE_TYPES + _PDF_FILE_TYPES,
    "robinhood_credit": _PDF_FILE_TYPES,
}


@dataclass(frozen=True)
class InstitutionDefinition:
    """A supported institution exposed in the UI and statement import pipeline."""

    slug: str
    name: str
    account_types: tuple[str, ...]
    parser_key: str | None = None
    auto_sync_key: str | None = None
    parser_config: dict[str, Any] = field(default_factory=dict)


def _inst(
    slug: str,
    name: str,
    account_types: tuple[str, ...],
    *,
    parser_key: str | None = None,
    auto_sync_key: str | None = None,
) -> InstitutionDefinition:
    resolved_parser_key = parser_key
    parser_config: dict[str, Any] = {}
    if resolved_parser_key:
        parser_config = dict(_PARSER_CONFIGS[resolved_parser_key])
    return InstitutionDefinition(
        slug=slug,
        name=name,
        account_types=account_types,
        parser_key=resolved_parser_key,
        auto_sync_key=auto_sync_key,
        parser_config=parser_config,
    )


INSTITUTIONS: dict[str, InstitutionDefinition] = {
    entry.slug: entry
    for entry in [
        _inst(
            "bank_of_america",
            "Bank of America",
            ("checking", "savings", "credit_card"),
            parser_key="bofa",
            auto_sync_key="bofa",
        ),
        _inst(
            "chase",
            "Chase",
            ("checking", "savings", "credit_card"),
            parser_key="chase",
            auto_sync_key="chase",
        ),
        _inst("citibank", "Citibank", ("credit_card",), parser_key="citi"),
        _inst("american_express", "American Express", ("checking", "credit_card"), parser_key="amex"),
        _inst(
            "marcus",
            "Marcus by Goldman Sachs",
            ("savings",),
            parser_key="marcus",
            auto_sync_key="marcus",
        ),
        _inst(
            "robinhood",
            "Robinhood",
            ("checking", "savings", "credit_card", "investment"),
            parser_key="robinhood_bank",
            auto_sync_key="robinhood",
        ),
        _inst("fidelity", "Fidelity", ("investment",), parser_key="fidelity"),
        _inst(
            "guideline",
            "Guideline",
            ("investment",),
            parser_key="guideline",
            auto_sync_key="guideline",
        ),
        _inst("other", "Other", ALL_ACCOUNT_TYPES),
    ]
}

# Legacy slugs that should still resolve to the same parser / auto-sync key.
_LEGACY_SLUG_ALIASES: dict[str, str] = {
    "bofa": "bank_of_america",
    "jpmorgan_chase": "chase",
    "robinhood_bank": "robinhood",
    "robinhood_investments": "robinhood",
}


def _canonical_slug(slug: str | None) -> str | None:
    if not slug:
        return None
    normalized = slug.lower()
    return _LEGACY_SLUG_ALIASES.get(normalized, normalized)


def list_institutions(*, include_other: bool = True) -> list[InstitutionDefinition]:
    """Return registry institutions sorted by name, with Other last."""
    entries = [inst for inst in INSTITUTIONS.values() if include_other or inst.slug != "other"]
    entries.sort(key=lambda item: (item.slug == "other", item.name.lower()))
    return entries


def get_institution(slug: str | None) -> InstitutionDefinition | None:
    canonical = _canonical_slug(slug)
    if not canonical:
        return None
    return INSTITUTIONS.get(canonical)


def parser_key_for_slug(slug: str | None) -> str | None:
    institution = get_institution(slug)
    if institution is None:
        return None
    return institution.parser_key


def get_parser_config(parser_key: str) -> dict[str, Any] | None:
    institution = next((item for item in INSTITUTIONS.values() if item.parser_key == parser_key), None)
    if institution is not None and institution.parser_config:
        return institution.parser_config
    return _PARSER_CONFIGS.get(parser_key)


def get_parser_reader(parser_key: str) -> Callable[[bytes], pd.DataFrame] | None:
    """Return a format-specific reader that materializes a DataFrame from raw bytes."""
    return PARSER_READERS.get(parser_key)


def parser_key_for_account(account) -> str | None:
    """Map an account's institution slug to a statement parser key."""
    institution = getattr(account, "institution", None)
    if institution is None:
        return None
    canonical = _canonical_slug(institution.slug)
    account_type = getattr(account, "account_type", None)
    if canonical == "robinhood":
        if account_type == "credit_card":
            return "robinhood_credit"
        if account_type == "investment":
            return "robinhood_investments"
    if canonical == "american_express" and account_type == "checking":
        return "amex_checking"
    return parser_key_for_slug(institution.slug)


def supported_file_types_for_parser(parser_key: str | None) -> list[str]:
    """Return allowed upload file types for a statement parser key."""
    if not parser_key:
        return list(_DEFAULT_FILE_TYPES)
    return list(_PARSER_FILE_TYPES.get(parser_key, _DEFAULT_FILE_TYPES))


def supported_extensions_for_parser(parser_key: str | None) -> set[str]:
    """Return allowed upload extensions (with leading dot) for a parser key."""
    return {f".{file_type}" for file_type in supported_file_types_for_parser(parser_key)}


def get_agent_institution_slug(account_institution_slug: str | None) -> str | None:
    institution = get_institution(account_institution_slug)
    if institution is None or institution.auto_sync_key is None:
        return None
    return institution.auto_sync_key


def institution_supports_agent_sync(account_institution_slug: str | None) -> bool:
    """Return True when the institution has a host bank-agent adapter."""
    return get_agent_institution_slug(account_institution_slug) is not None


def agent_flow_for_account(account_institution_slug: str | None, account_type: str) -> str | None:
    """Return the bank-agent flow for an account, or None when unsupported."""
    if not institution_supports_agent_sync(account_institution_slug):
        return None
    if account_type == "credit_card":
        return "credit_card"
    if account_institution_slug in {"guideline", "robinhood"} and account_type == "investment":
        return "investment_balance"
    if account_institution_slug == "marcus" and account_type == "savings":
        return "investment_balance"
    return "deposit"


def auto_sync_needs_storage_uri(flow: str | None) -> bool:
    """Statement download flows require a Google Drive folder per account."""
    return flow in {"deposit", "credit_card"}


def is_valid_account_type(slug: str | None, account_type: str) -> bool:
    institution = get_institution(slug)
    if institution is None:
        return account_type in ALL_ACCOUNT_TYPES
    return account_type in institution.account_types


def get_account_type_choices() -> list[dict[str, str]]:
    return [{"value": key, "label": label} for key, label in ACCOUNT_TYPE_LABELS.items()]


def _account_type_choices_for_institution(institution: InstitutionDefinition) -> list[dict[str, str]]:
    return [
        {"value": account_type, "label": ACCOUNT_TYPE_LABELS[account_type]}
        for account_type in institution.account_types
    ]


def _agent_flow_choices_for_institution(institution: InstitutionDefinition) -> list[dict[str, Any]]:
    return [
        {
            "account_type": account_type,
            "flow": agent_flow_for_account(institution.slug, account_type),
            "needs_storage": auto_sync_needs_storage_uri(agent_flow_for_account(institution.slug, account_type)),
        }
        for account_type in institution.account_types
    ]


def get_institution_field_choices() -> dict[str, Any]:
    """Payload for account form field choices."""
    institutions = []
    entity_choices = []
    for institution in list_institutions():
        payload = {
            "value": institution.slug,
            "label": institution.name,
            "account_types": _account_type_choices_for_institution(institution),
            "agent_flows": _agent_flow_choices_for_institution(institution),
        }
        institutions.append(payload)
        entity_choices.append({"value": institution.slug, "label": institution.name})

    return {
        "institutions": institutions,
        "type": get_account_type_choices(),
        "entity": entity_choices,
    }


def get_supported_institutions() -> list[dict[str, Any]]:
    """Institution metadata for statement import selectors."""
    entries: list[dict[str, Any]] = []
    for institution in list_institutions(include_other=False):
        if not institution.parser_key:
            continue
        file_types = list(_DEFAULT_FILE_TYPES)
        if institution.slug == "robinhood":
            file_types = sorted(set(file_types) | set(_PDF_FILE_TYPES))
        if institution.slug == "american_express":
            file_types = sorted(set(file_types) | set(_PDF_FILE_TYPES))
        entries.append(
            {
                "id": institution.parser_key,
                "slug": institution.slug,
                "display_name": institution.name,
                "account_types": list(institution.account_types),
                "file_types": file_types,
            }
        )
        if institution.slug == "robinhood" and "credit_card" in institution.account_types:
            entries.append(
                {
                    "id": "robinhood_credit",
                    "slug": institution.slug,
                    "display_name": f"{institution.name} Credit Card",
                    "account_types": ["credit_card"],
                    "file_types": list(_PDF_FILE_TYPES),
                }
            )
        if institution.slug == "robinhood" and "investment" in institution.account_types:
            entries.append(
                {
                    "id": "robinhood_investments",
                    "slug": institution.slug,
                    "display_name": f"{institution.name} Investments",
                    "account_types": ["investment"],
                    "file_types": list(_DEFAULT_FILE_TYPES),
                }
            )
        if institution.slug == "american_express" and "checking" in institution.account_types:
            entries.append(
                {
                    "id": "amex_checking",
                    "slug": institution.slug,
                    "display_name": f"{institution.name} Checking",
                    "account_types": ["checking"],
                    "file_types": list(_PDF_FILE_TYPES),
                }
            )
    return entries
