"""Submit a downloaded statement to the Richtato import API.

Uses HTTP Basic Auth against the docker-compose `backend` service. The Django
view accepts session or basic auth and an institution slug + account ID.
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
) -> dict:
    """Upload ``file_path`` for ``institution`` and return the API response payload."""

    if not config.richtato_user or not config.richtato_pass:
        raise ConfigError(
            "RICHTATO_USER and RICHTATO_PASS must be set so the automation can POST to the import API."
        )

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
                auth=(config.richtato_user, config.richtato_pass),
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
