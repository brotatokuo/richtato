"""Load due bank connections from the Richtato API.

This is the DB-backed counterpart to ``config._load_accounts_file``. The
automation container intentionally stays Django-free; instead it talks to
the backend's internal runner endpoints over HTTP using the same Basic Auth
service account already used by :mod:`scripts.automation.importer`.

Why an HTTP boundary?
- Lets the automation container ship as a slim Playwright image without
  Django, the postgres driver, or model imports.
- Mirrors how Plaid-style integrations are usually built: the headless
  worker only sees decrypted secrets at the moment it needs them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from loguru import logger

from scripts.automation.config import AutomationConfig
from scripts.automation.errors import ConfigError

DUE_CONNECTIONS_PATH = "/api/v1/bank-automation/runner/due-connections/"
RUN_OUTCOME_PATH = "/api/v1/bank-automation/runner/runs/{run_id}/outcome/"
REQUEST_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class DBAccount:
    """One account inside a fetched connection payload."""

    link_id: int
    slug: str
    flow: str
    activity_url: str
    external_account_token: str
    detected_account_name: str
    financial_account_id: int | None
    institution_slug: str


@dataclass
class DBConnection:
    """A connection lease returned by the runner-due endpoint.

    Holds the decrypted ``storage_state`` JSON and a ``run_id`` the runner
    must report back against. The ``storage_state_path`` property writes the
    JSON to a temp file just for the Playwright run; callers are responsible
    for unlinking it after the context closes.
    """

    connection_id: int
    run_id: int
    user_id: int
    institution_slug: str
    login_id: str
    nickname: str
    storage_state: str
    accounts: tuple[DBAccount, ...]
    _materialized_path: Path | None = None

    def materialize_storage_state(self) -> Path:
        """Write the decrypted storage_state to a temp file and return its path.

        The file lives only as long as this object; call :meth:`cleanup` when
        the Playwright context is closed to remove it.
        """

        if self._materialized_path is not None and self._materialized_path.exists():
            return self._materialized_path
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=f"_storage_state_{self.connection_id}.json",
            delete=False,
        ) as fh:
            fh.write(self.storage_state or "{}")
            self._materialized_path = Path(fh.name)
        return self._materialized_path

    def cleanup(self) -> None:
        if self._materialized_path is not None:
            try:
                self._materialized_path.unlink()
            except FileNotFoundError:
                pass
            self._materialized_path = None


def _auth_headers(config: AutomationConfig) -> dict[str, str]:
    if not config.richtato_runner_token:
        raise ConfigError(
            "RICHTATO_RUNNER_TOKEN must be set so the automation can call the runner API."
        )
    return {"Authorization": f"Token {config.richtato_runner_token}"}


def _coerce_accounts(raw_accounts) -> tuple[DBAccount, ...]:
    accounts: list[DBAccount] = []
    for entry in raw_accounts or []:
        accounts.append(
            DBAccount(
                link_id=int(entry["link_id"]),
                slug=str(entry.get("slug") or f"link_{entry['link_id']}"),
                flow=str(entry.get("flow") or "deposit"),
                activity_url=str(entry.get("activity_url") or ""),
                external_account_token=str(entry.get("external_account_token") or ""),
                detected_account_name=str(entry.get("detected_account_name") or ""),
                financial_account_id=(
                    int(entry["financial_account_id"])
                    if entry.get("financial_account_id") is not None
                    else None
                ),
                institution_slug=str(entry.get("institution_slug") or ""),
            )
        )
    return tuple(accounts)


def fetch_due_connections(
    config: AutomationConfig, *, force_all: bool = False
) -> list[DBConnection]:
    """Lease and fetch all due connections for the configured user.

    Atomically opens a ``BankAutomationRun`` per connection on the backend
    side so the runner has a stable ``run_id`` to report results against.
    """

    url = f"{config.richtato_base_url}{DUE_CONNECTIONS_PATH}"
    params = {"all": "1"} if force_all else {}
    try:
        response = requests.get(
            url,
            params=params,
            headers=_auth_headers(config),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ConfigError(f"Failed to fetch due connections: {exc}") from exc

    if response.status_code >= 400:
        raise ConfigError(
            f"Runner due-connections API returned {response.status_code}: {response.text[:300]}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise ConfigError(
            f"Runner due-connections API returned non-JSON: {exc}"
        ) from exc

    raw_connections = data.get("connections") or []
    connections: list[DBConnection] = []
    for entry in raw_connections:
        storage_state = entry.get("storage_state") or "{}"
        if isinstance(storage_state, dict):
            storage_state = json.dumps(storage_state)
        connections.append(
            DBConnection(
                connection_id=int(entry["connection_id"]),
                run_id=int(entry["run_id"]),
                user_id=int(entry["user_id"]),
                institution_slug=str(entry["institution_slug"]),
                login_id=str(entry["login_id"]),
                nickname=str(entry.get("nickname") or ""),
                storage_state=storage_state,
                accounts=_coerce_accounts(entry.get("accounts")),
            )
        )

    logger.info("Fetched {} due connection(s) from runner API", len(connections))
    return connections


def post_run_outcome(
    config: AutomationConfig,
    *,
    run_id: int,
    succeeded: bool,
    failure_kind: str = "",
    failure_reason: str = "",
    accounts_attempted: int = 0,
    accounts_succeeded: int = 0,
    statements_imported: int = 0,
) -> dict:
    """Report the outcome of a run back to the backend."""

    url = f"{config.richtato_base_url}{RUN_OUTCOME_PATH.format(run_id=run_id)}"
    payload = {
        "succeeded": succeeded,
        "failure_kind": failure_kind,
        "failure_reason": failure_reason,
        "accounts_attempted": accounts_attempted,
        "accounts_succeeded": accounts_succeeded,
        "statements_imported": statements_imported,
    }
    try:
        response = requests.post(
            url,
            json=payload,
            headers=_auth_headers(config),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.error("Failed to POST run outcome for run_id={}: {}", run_id, exc)
        return {"error": str(exc)}

    if response.status_code >= 400:
        logger.error(
            "Run outcome POST returned {} for run_id={}: {}",
            response.status_code,
            run_id,
            response.text[:300],
        )
        return {"error": response.text}

    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}
