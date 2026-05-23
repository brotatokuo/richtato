"""Configuration loading for the statement automation runner.

Two configuration sources are merged:

1. Environment variables (typically supplied via the project's ``.env`` file
   loaded by docker-compose). These cover credentials, schedule, and the
   legacy institution -> Richtato account ID mapping.
2. An optional ``accounts.json`` file under ``local_data/automation/`` that
   declares per-login browser sessions and per-account download targets. This
   is the path used by BoFA's multi-account flow (2 logins x N accounts each).
   The file is gitignored because it stores user-specific BoFA activity URLs.
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
ACCOUNTS_FILE_NAME = "accounts.json"

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

SUPPORTED_FLOWS: frozenset[str] = frozenset({"deposit", "credit_card"})


@dataclass(frozen=True)
class LoginSession:
    """A single saved browser session used to drive one or more accounts.

    ``storage_state_path`` points to a Playwright ``storage_state`` JSON
    produced by ``scripts/statement_downloader.py``. Multiple ``AutomationAccount``
    entries can reuse the same login without re-bootstrapping.
    """

    id: str
    storage_state_path: Path


@dataclass(frozen=True)
class AutomationAccount:
    """One downloadable account belonging to a ``LoginSession``.

    ``activity_url`` is the post-login URL that lands directly on the account's
    activity/download page (BoFA includes an opaque ``adx`` token here).
    ``flow`` selects which adapter variant drives the page after the goto.
    """

    slug: str
    login: str
    institution: str
    flow: str
    activity_url: str


@dataclass(frozen=True)
class AutomationConfig:
    """Resolved automation settings."""

    repo_root: Path
    storage_states_dir: Path
    statements_dir: Path
    state_file: Path
    logs_dir: Path
    accounts_file: Path

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
    logins: dict[str, LoginSession] = field(default_factory=dict)
    automation_accounts: tuple[AutomationAccount, ...] = field(default_factory=tuple)

    headless: bool = True

    def storage_state_path(self, institution: str) -> Path:
        return self.storage_states_dir / f"{institution}.json"

    def downloads_dir(self, slug: str) -> Path:
        return self.statements_dir / slug

    def find_account(self, slug: str) -> AutomationAccount | None:
        for account in self.automation_accounts:
            if account.slug == slug:
                return account
        return None

    def accounts_for_login(self, login_id: str) -> tuple[AutomationAccount, ...]:
        return tuple(a for a in self.automation_accounts if a.login == login_id)


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


def _resolve_storage_state(raw: str, automation_root: Path) -> Path:
    """Resolve a storage_state path from accounts.json.

    Relative paths are resolved against ``automation_root``
    (i.e. ``local_data/automation/``) so that the file can simply say
    ``storage_states/bofa_a.json``. Absolute paths are honoured as-is.
    """

    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    return automation_root / candidate


def _load_accounts_file(
    path: Path, automation_root: Path
) -> tuple[dict[str, LoginSession], tuple[AutomationAccount, ...]]:
    """Parse ``accounts.json`` into (logins, accounts).

    Returns empty containers when the file is missing or empty, leaving the
    legacy institution-based flow as the only path. Raises ``RuntimeError``
    when the file exists but cannot be parsed or references unknown logins
    so config issues fail loudly at startup.
    """

    if not path.exists():
        return {}, ()

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{path} is not valid JSON: {exc}") from exc

    logins_raw = raw.get("logins") or {}
    accounts_raw = raw.get("accounts") or []

    logins: dict[str, LoginSession] = {}
    for login_id, login_data in logins_raw.items():
        if not isinstance(login_data, dict):
            raise RuntimeError(
                f"{path}: login {login_id!r} must map to an object, got {type(login_data).__name__}"
            )
        storage_state = login_data.get("storage_state")
        if not storage_state:
            raise RuntimeError(f"{path}: login {login_id!r} is missing 'storage_state'")
        logins[login_id] = LoginSession(
            id=login_id,
            storage_state_path=_resolve_storage_state(storage_state, automation_root),
        )

    accounts: list[AutomationAccount] = []
    seen_slugs: set[str] = set()
    for entry in accounts_raw:
        if not isinstance(entry, dict):
            raise RuntimeError(
                f"{path}: each account entry must be an object, got {type(entry).__name__}"
            )
        slug = entry.get("slug")
        login_id = entry.get("login")
        institution = entry.get("institution")
        flow = entry.get("flow")
        activity_url = entry.get("activity_url")

        missing = [
            key
            for key, value in (
                ("slug", slug),
                ("login", login_id),
                ("institution", institution),
                ("flow", flow),
                ("activity_url", activity_url),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"{path}: account entry missing required keys {missing}: {entry!r}"
            )

        if slug in seen_slugs:
            raise RuntimeError(f"{path}: duplicate account slug {slug!r}")
        seen_slugs.add(slug)

        if login_id not in logins:
            raise RuntimeError(
                f"{path}: account {slug!r} references unknown login {login_id!r}"
            )
        if flow not in SUPPORTED_FLOWS:
            raise RuntimeError(
                f"{path}: account {slug!r} has unsupported flow {flow!r}; "
                f"expected one of {sorted(SUPPORTED_FLOWS)}"
            )
        if institution not in SUPPORTED_INSTITUTIONS:
            logger.warning(
                "{}: account {!r} institution {!r} is not in SUPPORTED_INSTITUTIONS; "
                "download will still run but a future import would reject it",
                path,
                slug,
                institution,
            )

        accounts.append(
            AutomationAccount(
                slug=slug,
                login=login_id,
                institution=institution,
                flow=flow,
                activity_url=activity_url,
            )
        )

    return logins, tuple(accounts)


def load_config(repo_root: Path | None = None) -> AutomationConfig:
    """Load the runtime configuration from environment variables."""

    load_dotenv()

    root = repo_root or Path(os.getenv("RICHTATO_REPO_ROOT", str(REPO_ROOT_DEFAULT)))
    automation_root = root / LOCAL_DATA_SUBPATH
    storage_states_dir = automation_root / "storage_states"
    logs_dir = automation_root / "logs"
    state_file = automation_root / "state.json"
    statements_dir = root / "local_data" / "statements"
    accounts_file = automation_root / ACCOUNTS_FILE_NAME

    storage_states_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    statements_dir.mkdir(parents=True, exist_ok=True)

    logins, automation_accounts = _load_accounts_file(accounts_file, automation_root)

    return AutomationConfig(
        repo_root=root,
        storage_states_dir=storage_states_dir,
        statements_dir=statements_dir,
        state_file=state_file,
        logs_dir=logs_dir,
        accounts_file=accounts_file,
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
        logins=logins,
        automation_accounts=automation_accounts,
        headless=_env_bool("AUTOMATION_HEADLESS", True),
    )
