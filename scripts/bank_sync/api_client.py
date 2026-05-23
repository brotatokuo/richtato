"""Thin HTTP wrapper around the Richtato bank-sync runner endpoints.

All requests authenticate with a DRF token belonging to a user with
``is_automation_runner=True`` (see ``backend/apps/bank_sync/management/
commands/create_automation_runner.py``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests
from loguru import logger

DEFAULT_TIMEOUT = 60


@dataclass
class AgentConfig:
    """Runtime configuration loaded from environment variables."""

    base_url: str
    runner_token: str
    poll_seconds: int
    headed_display: str
    storage_root: str

    @classmethod
    def from_env(cls) -> AgentConfig:
        base_url = os.getenv("RICHTATO_BASE_URL", "http://backend:8000").rstrip("/")
        token = os.getenv("RICHTATO_RUNNER_TOKEN", "")
        if not token:
            raise RuntimeError(
                "RICHTATO_RUNNER_TOKEN is required. Run "
                "`docker compose exec backend python manage.py create_automation_runner` "
                "to provision one."
            )
        return cls(
            base_url=base_url,
            runner_token=token,
            poll_seconds=int(os.getenv("BANK_SYNC_POLL_SECONDS", "30")),
            headed_display=os.getenv("DISPLAY", ":0"),
            storage_root=os.getenv("BANK_SYNC_DOWNLOAD_ROOT", "/app/local_data/bank_sync_downloads"),
        )


class APIClient:
    """Tiny REST client for the bank-sync runner endpoints."""

    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Token {cfg.runner_token}",
                "Accept": "application/json",
            }
        )

    def _url(self, path: str) -> str:
        return f"{self.cfg.base_url}{path}"

    def fetch_due_tasks(
        self,
        *,
        task_kinds: tuple[str, ...] | None = None,
    ) -> list[dict[str, Any]]:
        """Lease due tasks; returns an empty list when nothing is queued."""

        params: dict[str, str] = {}
        if task_kinds:
            params["task_kinds"] = ",".join(task_kinds)
        resp = self.session.get(
            self._url("/api/v1/bank-sync/runner/due-tasks/"),
            params=params or None,
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("tasks", [])

    def post_captured_session(
        self,
        run_id: int,
        *,
        storage_state: dict[str, Any],
        discovered_accounts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Report a successful interactive_login (cookies + discovered accounts)."""

        resp = self.session.post(
            self._url(f"/api/v1/bank-sync/runner/runs/{run_id}/captured-session/"),
            json={
                "storage_state": storage_state,
                "discovered_accounts": discovered_accounts,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def post_run_outcome(
        self,
        run_id: int,
        *,
        succeeded: bool,
        failure_kind: str = "",
        failure_reason: str = "",
        accounts_attempted: int = 0,
        accounts_succeeded: int = 0,
        statements_imported: int = 0,
    ) -> dict[str, Any]:
        """Report the final outcome of a SyncRun (success or failure)."""

        resp = self.session.post(
            self._url(f"/api/v1/bank-sync/runner/runs/{run_id}/outcome/"),
            json={
                "succeeded": succeeded,
                "failure_kind": failure_kind,
                "failure_reason": failure_reason,
                "accounts_attempted": accounts_attempted,
                "accounts_succeeded": accounts_succeeded,
                "statements_imported": statements_imported,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def import_statement(
        self,
        *,
        account_id: int,
        institution: str,
        file_path: str,
        statement_status: str = "provisional",
    ) -> dict[str, Any]:
        """POST a downloaded statement to Richtato's import endpoint in ``commit`` mode."""

        with open(file_path, "rb") as fh:
            resp = self.session.post(
                self._url("/api/v1/accounts/import-statement/"),
                data={
                    "account": account_id,
                    "institution": institution,
                    "mode": "commit",
                    "statement_status": statement_status,
                },
                files={"file": (os.path.basename(file_path), fh)},
                timeout=DEFAULT_TIMEOUT,
            )
        if not resp.ok:
            logger.error(
                "import-statement rejected: status={} body={}",
                resp.status_code,
                resp.text[:500],
            )
        resp.raise_for_status()
        return resp.json()
