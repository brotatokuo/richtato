"""Generate bank-agent configuration from Richtato accounts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from apps.financial_account.institutions.registry import get_agent_institution_slug
from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User


@dataclass(frozen=True)
class BankAgentConfigOptions:
    """Options for generated bank-agent config."""

    cadence: str = "daily"
    hour: int = 6
    nickname: str = "personal"
    include_all_supported: bool = False


class BankAgentConfigService:
    """Build the YAML/API payload consumed by the host bank-agent."""

    def build_for_user(self, user: User, options: BankAgentConfigOptions | None = None) -> dict[str, Any]:
        options = options or BankAgentConfigOptions()
        accounts = self._eligible_accounts(user, include_all_supported=options.include_all_supported)
        grouped: dict[str, list[FinancialAccount]] = {}

        for account in accounts:
            institution_slug = self._agent_institution_slug(account)
            if not institution_slug:
                continue
            grouped.setdefault(institution_slug, []).append(account)

        logins = []
        for institution_slug in sorted(grouped):
            login_accounts = [
                {
                    "name": account.name,
                    "flow": self._flow_for_account(account),
                    "storage_uri": account.resolved_storage_uri(),
                    "richtato_account_id": account.id,
                }
                for account in sorted(grouped[institution_slug], key=lambda item: item.name.lower())
            ]
            logins.append(
                {
                    "institution": institution_slug,
                    "nickname": options.nickname,
                    "cadence": options.cadence,
                    "hour": options.hour,
                    "accounts": login_accounts,
                }
            )

        return {
            "version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "user_id": user.id,
            "source": "richtato_accounts",
            "logins": logins,
        }

    def _eligible_accounts(self, user: User, *, include_all_supported: bool) -> list[FinancialAccount]:
        queryset = FinancialAccount.objects.filter(user=user, is_active=True, institution__isnull=False).select_related(
            "institution", "user"
        )
        if not include_all_supported:
            queryset = queryset.filter(sync_mode="auto")
        return list(queryset)

    def _agent_institution_slug(self, account: FinancialAccount) -> str | None:
        slug = account.institution.slug if account.institution else ""
        return get_agent_institution_slug(slug)

    def _flow_for_account(self, account: FinancialAccount) -> str:
        return "credit_card" if account.account_type == "credit_card" else "deposit"
