"""Per-user envelope encryption + agent payload helpers."""

from __future__ import annotations

import json

from django.utils import timezone

from apps.bank_sync.models import BankLogin, SyncRun


def store_storage_state(login: BankLogin, storage_state) -> BankLogin:
    """Encrypt and persist a Playwright ``storage_state`` payload on ``login``.

    Accepts either a JSON-serialisable dict or a pre-serialised string. The
    encrypted value is bound to the login's owning user so the per-user key
    is used and a DB leak alone does not recover plaintext cookies.
    """

    blob = storage_state if isinstance(storage_state, str) else json.dumps(storage_state)
    login.set_storage_state(blob)
    login.cookies_captured_at = timezone.now()
    login.save(
        update_fields=[
            "storage_state_encrypted",
            "cookies_captured_at",
            "updated_at",
        ]
    )
    return login


def get_storage_state(login: BankLogin) -> str:
    """Return the decrypted ``storage_state`` JSON string."""

    return login.storage_state


def serialize_runner_task(run: SyncRun) -> dict:
    """Build the JSON payload the agent consumes for one leased SyncRun.

    Includes decrypted ``storage_state`` and per-account ``activity_url`` so
    the agent can drive Playwright without round-tripping for secrets. Only
    the runner endpoint exposes this payload; end-user endpoints never
    return plaintext cookies or URLs.
    """

    login = run.bank_login
    accounts = []
    for synced in login.synced_accounts.filter(enabled=True).select_related("financial_account"):
        accounts.append(
            {
                "synced_account_id": synced.id,
                "financial_account_id": synced.financial_account_id,
                "flow": synced.flow,
                "activity_url": synced.activity_url,
                "external_account_token": synced.external_account_token,
                "detected_account_name": synced.detected_account_name,
            }
        )
    return {
        "run_id": run.id,
        "task_kind": run.task_kind,
        "bank_login_id": login.id,
        "user_id": login.user_id,
        "institution_slug": login.institution.slug,
        "institution_name": login.institution.name,
        "nickname": login.nickname,
        "storage_state": get_storage_state(login) if run.task_kind != "interactive_login" else "",
        "accounts": accounts,
    }
