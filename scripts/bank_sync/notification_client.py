"""Post bank-agent failure events back to Richtato."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urljoin

from loguru import logger

from scripts.bank_sync.agent_store import AgentStore
from scripts.bank_sync.errors import parse_failure_kind, strip_failure_prefix


def post_failure_event(
    *,
    store: AgentStore,
    login_id: int,
    outcome: Any,
    event_type: str,
) -> None:
    """Best-effort failure notification post; never fails the sync run."""

    if not getattr(outcome, "failure_reason", "") and not getattr(outcome, "account_failures", []):
        return

    token = os.environ.get("RICHTATO_API_TOKEN", "")
    if not token:
        logger.info("Skipping Richtato failure event: RICHTATO_API_TOKEN is not set")
        return

    try:
        import requests
    except ModuleNotFoundError:
        logger.warning("Skipping Richtato failure event: requests is not installed")
        return

    login = store.get_login(login_id)
    account_failure = (getattr(outcome, "account_failures", []) or [None])[0]
    account = store.get_account(account_failure.account_id) if account_failure else None
    failure_kind = getattr(outcome, "failure_kind", None) or parse_failure_kind(getattr(outcome, "failure_reason", ""))
    message = strip_failure_prefix(getattr(outcome, "failure_reason", "")) or (
        account_failure.message if account_failure else "Bank sync failed."
    )

    base_url = os.environ.get("RICHTATO_API_BASE_URL") or "http://127.0.0.1:8000/api/v1"
    endpoint = urljoin(base_url.rstrip("/") + "/", "accounts/bank-agent-events/")
    payload = {
        "event_type": event_type,
        "login_id": login_id,
        "institution_slug": login.institution_slug if login else "",
        "nickname": login.nickname if login else "",
        "failure_kind": failure_kind.value if failure_kind else "unknown",
        "message": message[:1000],
        "run_status": getattr(outcome, "run_status", ""),
        "account_id": account.id if account else None,
        "richtato_account_id": account.richtato_account_id if account else None,
    }

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Authorization": f"Token {token}"},
            timeout=15,
        )
    except requests.RequestException as exc:
        logger.warning("Failed to post Richtato failure event: {}", exc)
        return

    if response.status_code >= 400:
        logger.warning(
            "Richtato failure event rejected status={} body={}",
            response.status_code,
            response.text[:300],
        )
