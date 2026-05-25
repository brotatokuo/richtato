"""Build sync-setup payloads for the Setup → Sync UI."""

from __future__ import annotations

from typing import Any

from apps.financial_account.institutions.registry import (
    agent_flow_for_account,
    auto_sync_needs_storage_uri,
)
from apps.financial_account.models import FinancialAccount
from apps.financial_account.services.bank_agent_config_service import BankAgentConfigService
from apps.richtato_user.models import User


class BankSyncSetupService:
    """Summarize per-account sync settings and generated agent config."""

    def build_for_user(self, user: User) -> dict[str, Any]:
        accounts = (
            FinancialAccount.objects.filter(user=user, is_active=True, institution__isnull=False)
            .select_related("institution")
            .order_by("name")
        )
        rows: list[dict[str, Any]] = []
        for account in accounts:
            institution_slug = account.institution.slug if account.institution else None
            flow = agent_flow_for_account(institution_slug, account.account_type)
            resolved_storage_uri = account.resolved_storage_uri()
            rows.append(
                {
                    "id": account.id,
                    "name": account.name,
                    "institution_slug": institution_slug,
                    "institution_name": account.institution.name if account.institution else "",
                    "account_type": account.account_type,
                    "account_type_display": account.get_account_type_display(),
                    "sync_mode": account.sync_mode,
                    "agent_sync_supported": flow is not None,
                    "agent_flow": flow,
                    "needs_storage_for_auto": auto_sync_needs_storage_uri(flow),
                    "has_storage_uri": bool(resolved_storage_uri),
                    "resolved_storage_uri": resolved_storage_uri,
                }
            )

        return {
            "accounts": rows,
            "agent_config": BankAgentConfigService().build_for_user(user),
        }
