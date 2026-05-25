"""Generate bank-agent configuration from Richtato accounts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from apps.financial_account.institutions.registry import agent_flow_for_account, get_agent_institution_slug
from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User


@dataclass(frozen=True)
class BankAgentConfigOptions:
    """Options for generated bank-agent config."""

    nickname: str = "personal"
    include_all_supported: bool = False


class BankAgentConfigService:
    """Build the YAML/API payload consumed by the host bank-agent."""

    def build_for_user(self, user: User, options: BankAgentConfigOptions | None = None) -> dict[str, Any]:
        options = options or BankAgentConfigOptions()
        accounts = self._eligible_accounts(user, include_all_supported=options.include_all_supported)
        grouped: dict[tuple[str, str, int], list[FinancialAccount]] = {}

        for account in accounts:
            institution_slug = self._agent_institution_slug(account)
            if not institution_slug:
                continue
            schedule_key = (
                institution_slug,
                account.agent_cadence,
                account.agent_sync_hour,
            )
            grouped.setdefault(schedule_key, []).append(account)

        institution_login_counts: dict[str, int] = defaultdict(int)
        logins = []
        for institution_slug, cadence, hour in sorted(grouped):
            group_accounts = sorted(grouped[(institution_slug, cadence, hour)], key=lambda item: item.name.lower())
            institution_login_counts[institution_slug] += 1
            login_index = institution_login_counts[institution_slug]
            if login_index == 1:
                nickname = options.nickname
            else:
                nickname = f"{options.nickname}-{group_accounts[0].id}"

            login_accounts = []
            for account in group_accounts:
                account_payload = {
                    "name": account.name,
                    "flow": self._flow_for_account(account),
                    "storage_uri": account.resolved_storage_uri(),
                    "richtato_account_id": account.id,
                }
                activity_url = account.agent_activity_url
                if activity_url:
                    account_payload["activity_url"] = activity_url
                login_accounts.append(account_payload)
            logins.append(
                {
                    "institution": institution_slug,
                    "nickname": nickname,
                    "cadence": cadence,
                    "hour": hour,
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
        institution_slug = account.institution.slug if account.institution else ""
        flow = agent_flow_for_account(institution_slug, account.account_type)
        return flow or "deposit"
