"""Export generated bank-agent config from Richtato accounts."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.financial_account.services.bank_agent_config_service import BankAgentConfigOptions, BankAgentConfigService
from apps.financial_account.services.bank_agent_setup_export_service import BankAgentSetupExportService
from apps.richtato_user.models import User


class Command(BaseCommand):
    help = "Export generated bank-agent config for a user's active auto-sync accounts."

    def add_arguments(self, parser):
        parser.add_argument("--user-id", type=int, required=True, help="Richtato user ID to export.")
        parser.add_argument("--output", type=str, default="", help="Optional path to write instead of stdout.")
        parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
        parser.add_argument("--nickname", default="personal")
        parser.add_argument(
            "--all-supported",
            action="store_true",
            help="Include all active accounts with supported institutions, not just sync_mode=auto.",
        )
        parser.add_argument(
            "--with-credentials",
            action="store_true",
            help="Include RICHTATO_API_TOKEN and BANK_AGENT_FERNET_KEY in YAML output.",
        )

    def handle(self, *args, **options):
        user = User.objects.filter(id=options["user_id"]).first()
        if not user:
            raise CommandError(f"User not found: {options['user_id']}")

        if options["format"] == "json":
            config = BankAgentConfigService().build_for_user(
                user,
                BankAgentConfigOptions(
                    nickname=options["nickname"],
                    include_all_supported=options["all_supported"],
                ),
            )
            rendered = json.dumps(config, indent=2, sort_keys=True)
        else:
            rendered = BankAgentSetupExportService().build_yaml_for_user(
                user,
                include_credentials=options["with_credentials"],
                include_all_supported=options["all_supported"],
                nickname=options["nickname"],
            )

        output_path = options["output"]
        if output_path:
            Path(output_path).write_text(rendered)
            self.stdout.write(self.style.SUCCESS(f"Wrote bank-agent config to {output_path}"))
            return

        self.stdout.write(rendered)
