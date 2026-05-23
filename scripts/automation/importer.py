"""Submit a downloaded statement to the Richtato import API.

Uses DRF Token Auth against the docker-compose ``backend`` service. The
``RICHTATO_RUNNER_TOKEN`` must belong to a Django user with
``is_automation_runner=True`` so the import view allows cross-user account
lookups.
"""

from __future__ import annotations

from pathlib import Path

import requests
from loguru import logger

from scripts.automation.config import AutomationConfig
from scripts.automation.errors import ConfigError, ImportRejected

IMPORT_PATH = "/api/v1/accounts/import-statement/"
REQUEST_TIMEOUT_SECONDS = 90


def submit_statement(
    config: AutomationConfig,
    institution: str,
    file_path: Path,
    *,
    account_id: int | None = None,
) -> dict:
    """Upload ``file_path`` for ``institution`` and return the API response payload.

    ``account_id`` overrides the static AUTOMATION_ACCOUNT_IDS mapping; the
    DB-driven runner passes it explicitly per ``BankAccountLink``.
    """

    if not config.richtato_runner_token:
        raise ConfigError(
            "RICHTATO_RUNNER_TOKEN must be set so the automation can POST to the import API."
        )

    if account_id is None:
        account_id = config.account_ids.get(institution)
    if account_id is None:
        raise ConfigError(
            f"No account ID configured for institution {institution!r}. Set AUTOMATION_ACCOUNT_IDS in .env."
        )

    if not file_path.exists():
        raise ImportRejected(f"Downloaded file disappeared before import: {file_path}")

    url = f"{config.richtato_base_url}{IMPORT_PATH}"
    logger.info("Submitting {} for {} to {}", file_path.name, institution, url)

    with file_path.open("rb") as handle:
        try:
            response = requests.post(
                url,
                files={"file": (file_path.name, handle)},
                data={
                    "account": str(account_id),
                    "institution": institution,
                    "mode": "commit",
                    "statement_status": "provisional",
                },
                headers={"Authorization": f"Token {config.richtato_runner_token}"},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise ImportRejected(f"HTTP error contacting Richtato API: {exc}") from exc

    if response.status_code >= 400:
        body_preview = response.text[:500].replace("\n", " ")
        raise ImportRejected(
            f"Import API returned {response.status_code}: {body_preview}"
        )

    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}
