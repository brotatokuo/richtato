"""Configuration loading for the statement automation runner.

All configuration is sourced from environment variables (typically supplied via
the project's `.env` file, mounted into the container via docker-compose).
Institution -> Richtato account ID mapping is read from a JSON-formatted env
variable so it can be edited without rebuilding the image.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

REPO_ROOT_DEFAULT = Path("/app")
LOCAL_DATA_SUBPATH = "local_data/automation"

SUPPORTED_INSTITUTIONS: tuple[str, ...] = (
    "bofa",
    "marcus",
    "amex",
    "robinhood_bank",
    "fidelity",
    "robinhood_investments",
    "guideline",
    "chase",
)


@dataclass(frozen=True)
class AutomationConfig:
    """Resolved automation settings."""

    repo_root: Path
    storage_states_dir: Path
    statements_dir: Path
    state_file: Path
    logs_dir: Path

    richtato_base_url: str
    richtato_user: str
    richtato_pass: str

    gmail_user: str
    gmail_app_password: str
    alert_to: str

    run_time: str
    run_timezone: str
    stale_threshold_days: int

    enabled_institutions: tuple[str, ...]
    account_ids: dict[str, int] = field(default_factory=dict)

    headless: bool = True

    def storage_state_path(self, institution: str) -> Path:
        return self.storage_states_dir / f"{institution}.json"

    def downloads_dir(self, institution: str) -> Path:
        return self.statements_dir / institution


def _env_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning(
            "Invalid integer for {}={!r}; falling back to {}", key, raw, default
        )
        return default


def _parse_account_ids(raw: str | None) -> dict[str, int]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"AUTOMATION_ACCOUNT_IDS is not valid JSON: {exc}") from exc
    result: dict[str, int] = {}
    for slug, account_id in parsed.items():
        if slug not in SUPPORTED_INSTITUTIONS:
            logger.warning(
                "AUTOMATION_ACCOUNT_IDS contains unknown institution {!r}; ignoring",
                slug,
            )
            continue
        result[slug] = int(account_id)
    return result


def _parse_enabled(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return SUPPORTED_INSTITUTIONS
    requested = tuple(slug.strip() for slug in raw.split(",") if slug.strip())
    unknown = [slug for slug in requested if slug not in SUPPORTED_INSTITUTIONS]
    if unknown:
        logger.warning(
            "AUTOMATION_INSTITUTIONS contains unknown slugs {}; ignoring", unknown
        )
    return tuple(slug for slug in requested if slug in SUPPORTED_INSTITUTIONS)


def load_config(repo_root: Path | None = None) -> AutomationConfig:
    """Load the runtime configuration from environment variables."""

    load_dotenv()

    root = repo_root or Path(os.getenv("RICHTATO_REPO_ROOT", str(REPO_ROOT_DEFAULT)))
    automation_root = root / LOCAL_DATA_SUBPATH
    storage_states_dir = automation_root / "storage_states"
    logs_dir = automation_root / "logs"
    state_file = automation_root / "state.json"
    statements_dir = root / "local_data" / "statements"

    storage_states_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    statements_dir.mkdir(parents=True, exist_ok=True)

    return AutomationConfig(
        repo_root=root,
        storage_states_dir=storage_states_dir,
        statements_dir=statements_dir,
        state_file=state_file,
        logs_dir=logs_dir,
        richtato_base_url=os.getenv("RICHTATO_BASE_URL", "http://backend:8000").rstrip(
            "/"
        ),
        richtato_user=os.getenv("RICHTATO_USER", ""),
        richtato_pass=os.getenv("RICHTATO_PASS", ""),
        gmail_user=os.getenv("GMAIL_USER", ""),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
        alert_to=os.getenv("ALERT_TO", ""),
        run_time=os.getenv("RUN_TIME", "06:00"),
        run_timezone=os.getenv("RUN_TIMEZONE", "America/Los_Angeles"),
        stale_threshold_days=_env_int("STALE_THRESHOLD_DAYS", 3),
        enabled_institutions=_parse_enabled(os.getenv("AUTOMATION_INSTITUTIONS")),
        account_ids=_parse_account_ids(os.getenv("AUTOMATION_ACCOUNT_IDS")),
        headless=_env_bool("AUTOMATION_HEADLESS", True),
    )
