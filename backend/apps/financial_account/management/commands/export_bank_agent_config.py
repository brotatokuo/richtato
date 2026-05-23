"""Export generated bank-agent config from Richtato accounts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.financial_account.services.bank_agent_config_service import BankAgentConfigOptions, BankAgentConfigService
from apps.richtato_user.models import User


class Command(BaseCommand):
    help = "Export generated bank-agent config for a user's active auto-sync accounts."

    def add_arguments(self, parser):
        parser.add_argument("--user-id", type=int, required=True, help="Richtato user ID to export.")
        parser.add_argument("--output", type=str, default="", help="Optional path to write instead of stdout.")
        parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
        parser.add_argument("--cadence", choices=["manual", "daily", "weekly", "monthly"], default="daily")
        parser.add_argument("--hour", type=int, default=6)
        parser.add_argument("--nickname", default="personal")
        parser.add_argument(
            "--all-supported",
            action="store_true",
            help="Include all active accounts with supported institutions, not just sync_mode=auto.",
        )

    def handle(self, *args, **options):
        if options["hour"] < 0 or options["hour"] > 23:
            raise CommandError("--hour must be between 0 and 23")

        user = User.objects.filter(id=options["user_id"]).first()
        if not user:
            raise CommandError(f"User not found: {options['user_id']}")

        config = BankAgentConfigService().build_for_user(
            user,
            BankAgentConfigOptions(
                cadence=options["cadence"],
                hour=options["hour"],
                nickname=options["nickname"],
                include_all_supported=options["all_supported"],
            ),
        )
        rendered = json.dumps(config, indent=2, sort_keys=True) if options["format"] == "json" else _dump_yaml(config)

        output_path = options["output"]
        if output_path:
            Path(output_path).write_text(rendered)
            self.stdout.write(self.style.SUCCESS(f"Wrote bank-agent config to {output_path}"))
            return

        self.stdout.write(rendered)


def _dump_yaml(config: dict[str, Any]) -> str:
    """Render the small bank-agent config shape without requiring PyYAML."""

    lines = [
        "# Generated from Richtato accounts. Do not edit by hand unless debugging.",
        f"version: {config['version']}",
        f"generated_at: {_quote(config['generated_at'])}",
        f"user_id: {config['user_id']}",
        f"source: {_quote(config['source'])}",
        "logins:",
    ]
    for login in config["logins"]:
        lines.extend(
            [
                f"  - institution: {_quote(login['institution'])}",
                f"    nickname: {_quote(login['nickname'])}",
                f"    cadence: {_quote(login['cadence'])}",
                f"    hour: {login['hour']}",
                "    accounts:",
            ]
        )
        for account in login["accounts"]:
            lines.extend(
                [
                    f"      - name: {_quote(account['name'])}",
                    f"        flow: {_quote(account['flow'])}",
                    f"        storage_uri: {_quote(account['storage_uri'])}",
                    f"        richtato_account_id: {account['richtato_account_id']}",
                ]
            )
    if not config["logins"]:
        lines.append("  []")
    return "\n".join(lines) + "\n"


def _quote(value: str) -> str:
    return json.dumps(value)
