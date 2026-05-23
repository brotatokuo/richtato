"""One-shot migration of local_data/automation/accounts.json into the DB.

Used by the developer who originally seeded the file-based runner. Reads
``accounts.json`` plus the matching ``storage_states/<login>.json`` files,
encrypts them with ``apps.bank_automation.encryption``, and creates one
``BankConnection`` per login with ``BankAccountLink`` rows for each
account entry.

Idempotent on ``(user, institution, login_id)`` so running it twice will
update existing rows rather than create duplicates.
"""

from __future__ import annotations

import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.bank_automation.services.connection_service import (
    CapturedAccount,
    CapturedSession,
    ingest_captured_session,
)


class Command(BaseCommand):
    help = (
        "Migrate local_data/automation/accounts.json into the bank_automation "
        "tables for the given user. Use after upgrading from the file-based runner."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            required=True,
            help="Richtato username that owns the resulting BankConnection rows.",
        )
        parser.add_argument(
            "--accounts-file",
            default="/app/local_data/automation/accounts.json",
            help="Path to accounts.json (default: /app/local_data/automation/accounts.json).",
        )
        parser.add_argument(
            "--storage-states-dir",
            default="/app/local_data/automation/storage_states",
            help="Directory holding <login>.json storage_state files.",
        )
        parser.add_argument(
            "--account-id-map",
            default="",
            help=(
                "Optional JSON mapping of account slug -> Richtato FinancialAccount id, "
                "e.g. '{\"bofa_a_checking\": 12}'. Slugs missing from the map land "
                "without an account binding and have to be linked in the UI."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would happen without writing to the database.",
        )

    def handle(self, *args, **options):
        username = options["username"]
        accounts_file = Path(options["accounts_file"])
        storage_dir = Path(options["storage_states_dir"])
        dry_run = bool(options["dry_run"])

        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=username)
        except user_model.DoesNotExist as exc:
            raise CommandError(f"User {username!r} not found") from exc

        if not accounts_file.exists():
            raise CommandError(f"Accounts file not found: {accounts_file}")

        try:
            raw = json.loads(accounts_file.read_text())
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {accounts_file}: {exc}") from exc

        try:
            account_id_map = json.loads(options["account_id_map"]) if options["account_id_map"] else {}
        except json.JSONDecodeError as exc:
            raise CommandError(f"--account-id-map must be valid JSON: {exc}") from exc

        logins = raw.get("logins") or {}
        accounts = raw.get("accounts") or []

        accounts_by_login: dict[str, list[dict]] = {}
        for entry in accounts:
            accounts_by_login.setdefault(entry["login"], []).append(entry)

        for login_id, login_data in logins.items():
            login_accounts = accounts_by_login.get(login_id, [])
            if not login_accounts:
                self.stdout.write(self.style.WARNING(f"login={login_id} has no accounts; skipping"))
                continue

            storage_state_relpath = login_data.get("storage_state")
            if not storage_state_relpath:
                self.stdout.write(self.style.WARNING(f"login={login_id} has no storage_state; skipping"))
                continue

            storage_path = (
                Path(storage_state_relpath)
                if Path(storage_state_relpath).is_absolute()
                else accounts_file.parent / storage_state_relpath
            )
            if not storage_path.exists():
                # Try the explicit storage-states dir as a fallback.
                fallback = storage_dir / Path(storage_state_relpath).name
                if fallback.exists():
                    storage_path = fallback
                else:
                    self.stdout.write(
                        self.style.WARNING(f"login={login_id} storage state {storage_path} not found; skipping")
                    )
                    continue

            try:
                storage_state_json = storage_path.read_text()
                # Sanity-check it's parseable.
                json.loads(storage_state_json)
            except (OSError, json.JSONDecodeError) as exc:
                self.stdout.write(
                    self.style.WARNING(f"login={login_id}: cannot read storage state {storage_path}: {exc}")
                )
                continue

            institution_slug = login_accounts[0].get("institution") or "bofa"
            captured_accounts = tuple(
                CapturedAccount(
                    flow=entry.get("flow", "deposit"),
                    activity_url=entry.get("activity_url", ""),
                    detected_account_name=entry.get("slug", ""),
                    financial_account_id=account_id_map.get(entry.get("slug")),
                )
                for entry in login_accounts
                if not entry.get("activity_url", "").startswith("REPLACE_")
            )

            if not captured_accounts:
                self.stdout.write(
                    self.style.WARNING(f"login={login_id}: no accounts with non-placeholder activity URLs; skipping")
                )
                continue

            self.stdout.write(f"login={login_id}: {len(captured_accounts)} account(s) -> ingest_captured_session")

            if dry_run:
                continue

            connection = ingest_captured_session(
                user=user,
                capture=CapturedSession(
                    institution_slug=institution_slug,
                    login_id=login_id,
                    storage_state=storage_state_json,
                    accounts=captured_accounts,
                    nickname=f"{institution_slug.upper()} ({login_id})",
                ),
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"login={login_id}: created/updated BankConnection id={connection.id} "
                    f"with {len(connection.account_links.all())} account link(s)"
                )
            )

        self.stdout.write(self.style.SUCCESS("Done."))
