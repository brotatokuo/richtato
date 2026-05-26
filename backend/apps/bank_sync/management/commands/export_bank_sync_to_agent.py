"""Export the legacy ``apps.bank_sync`` vault into a bank-agent JSON payload.

Phase-3 migration helper. The export contains:

* one entry per ``BankLogin`` with its decrypted ``storage_state`` (the
  agent re-encrypts it under ``BANK_AGENT_FERNET_KEY``).
* one entry per ``SyncedAccount`` carrying its decrypted activity URL and
  the bound ``FinancialAccount``'s ``resolved_storage_uri``.

Pipe the output into ``python -m scripts.bank_sync.agent import <file>``
to seed the agent SQLite. Once you've verified the agent is downloading
correctly, the legacy bank_sync app + runner API can be deleted.
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.bank_sync.models import BankLogin, SyncedAccount


class Command(BaseCommand):
    help = "Export legacy bank_sync data to a JSON payload importable by the bank-agent CLI."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="-",
            help="Output path (or '-' for stdout, the default).",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            default=None,
            help="Limit export to a single user.",
        )
        parser.add_argument(
            "--include-disabled",
            action="store_true",
            help="Include disabled logins (skipped by default).",
        )

    def handle(self, *args, **options):
        login_qs = BankLogin.objects.select_related("user", "institution").order_by("id")
        if options.get("user_id"):
            login_qs = login_qs.filter(user_id=options["user_id"])
        if not options["include_disabled"]:
            login_qs = login_qs.exclude(status="disabled")

        synced_qs = SyncedAccount.objects.select_related(
            "bank_login",
            "financial_account",
            "financial_account__institution",
        )

        payload: dict[str, list[dict]] = {"logins": [], "accounts": []}

        for login in login_qs:
            storage_state = ""
            try:
                storage_state = login.storage_state
            except Exception as exc:  # pragma: no cover - decrypt failure
                self.stderr.write(self.style.WARNING(f"Could not decrypt storage_state for login {login.id}: {exc}"))
            payload["logins"].append(
                {
                    "id": login.id,
                    "institution_slug": login.institution.slug,
                    "nickname": login.nickname,
                    "cadence": login.cadence,
                    "preferred_run_hour_local": login.preferred_run_hour_local,
                    "status": login.status,
                    # Plaintext: the agent will re-encrypt with its own key.
                    "storage_state_plaintext": storage_state,
                    "cookies_captured_at": (
                        login.cookies_captured_at.isoformat() if login.cookies_captured_at else None
                    ),
                }
            )

            for synced in synced_qs.filter(bank_login=login):
                account = synced.financial_account
                try:
                    activity_url = synced.activity_url
                except Exception as exc:  # pragma: no cover - decrypt failure
                    self.stderr.write(
                        self.style.WARNING(f"Could not decrypt activity_url for synced_account {synced.id}: {exc}")
                    )
                    activity_url = ""
                payload["accounts"].append(
                    {
                        "id": synced.id,
                        "login_id": login.id,
                        "detected_account_name": synced.detected_account_name,
                        "activity_url_plaintext": activity_url,
                        "flow": synced.flow,
                        "storage_uri": account.resolved_storage_uri(),
                        "enabled": synced.enabled,
                    }
                )

        # Render with sorted keys for deterministic diffs.
        text = json.dumps(payload, indent=2, sort_keys=True)

        if options["output"] == "-":
            self.stdout.write(text)
        else:
            Path(options["output"]).write_text(text)
            self.stdout.write(self.style.SUCCESS(f"Wrote {options['output']}"))

        self.stderr.write(
            f"Exported {len(payload['logins'])} login(s) and {len(payload['accounts'])} account(s).\n"
            "Next step on the host:\n"
            "  python -m scripts.bank_sync.agent import <file>\n"
            "Make sure BANK_AGENT_FERNET_KEY is set first."
        )
