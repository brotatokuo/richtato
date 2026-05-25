"""Export a complete bank-agent setup file for the host CLI."""

from __future__ import annotations

from typing import Any

from apps.financial_account.services.bank_agent_config_service import BankAgentConfigOptions, BankAgentConfigService
from apps.financial_account.services.bank_agent_yaml import dump_bank_agent_setup_yaml
from apps.richtato_user.models import User
from apps.richtato_user.services.bank_agent_credentials_service import get_bank_agent_credentials


class BankAgentSetupExportService:
    """Build YAML setup files with credentials and login config."""

    def build_yaml_for_user(
        self,
        user: User,
        *,
        include_credentials: bool = True,
        include_all_supported: bool = False,
        nickname: str = "personal",
    ) -> str:
        config = BankAgentConfigService().build_for_user(
            user,
            BankAgentConfigOptions(
                nickname=nickname,
                include_all_supported=include_all_supported,
            ),
        )
        env: dict[str, str] | None = None
        if include_credentials:
            credentials = get_bank_agent_credentials(user)
            env = {
                "RICHTATO_API_TOKEN": credentials["token"],
                "BANK_AGENT_FERNET_KEY": credentials["fernet_key"],
            }
        return dump_bank_agent_setup_yaml(config=config, env=env)

    def build_config_for_user(
        self,
        user: User,
        *,
        include_all_supported: bool = False,
        nickname: str = "personal",
    ) -> dict[str, Any]:
        return BankAgentConfigService().build_for_user(
            user,
            BankAgentConfigOptions(
                nickname=nickname,
                include_all_supported=include_all_supported,
            ),
        )
