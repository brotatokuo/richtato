"""Agent-local persistence: SQLite vault for logins, accounts, and runs.

The bank-agent runs as an independent host process. It does not share a
database with Richtato's Django backend; the only contract between the
two is the storage filesystem path each account writes to.

All sensitive fields (cookie ``storage_state`` and bank activity URLs)
are Fernet-encrypted at rest with a key from ``BANK_AGENT_FERNET_KEY``.
Schedule and metadata columns are stored plaintext so the CLI can show
``status`` without unlocking secrets.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from scripts.bank_sync.encryption import decrypt_text, encrypt_text

DEFAULT_DB_PATH = Path(
    os.environ.get(
        "BANK_AGENT_DB_PATH",
        str(Path(__file__).resolve().parents[2] / "local_data" / "bank-agent" / "agent.db"),
    )
)

CADENCES = ("manual", "daily", "weekly", "monthly")
LOGIN_STATUSES = ("pending_login", "active", "needs_reauth", "disabled", "error")
ACCOUNT_FLOWS = ("deposit", "credit_card", "investment_balance")
RUN_KINDS = ("interactive_login", "scheduled_download", "manual_download")
RUN_STATUSES = ("queued", "running", "completed", "failed", "partial")


@dataclass
class Login:
    """One bank login: institution + encrypted cookies + cadence."""

    id: int
    institution_slug: str
    nickname: str
    status: str
    cookies_captured_at: str | None
    cadence: str
    preferred_run_hour_local: int
    next_run_at: str | None
    last_run_at: str | None
    last_success_at: str | None
    last_failure_reason: str
    storage_state_encrypted: str
    created_at: str

    @property
    def storage_state(self) -> str:
        """Decrypt and return the Playwright storage_state JSON, or empty string."""
        return decrypt_text(self.storage_state_encrypted)


@dataclass
class Account:
    """One bank-side account bound to a login + storage URI."""

    id: int
    login_id: int
    detected_account_name: str
    activity_url_encrypted: str
    flow: str
    storage_uri: str
    richtato_account_id: int | None
    enabled: bool
    last_success_at: str | None
    created_at: str

    @property
    def activity_url(self) -> str:
        """Decrypt and return the bank-specific activity URL."""
        return decrypt_text(self.activity_url_encrypted)


@dataclass
class Run:
    """One execution record (login, download, etc.)."""

    id: int
    login_id: int
    kind: str
    status: str
    started_at: str
    finished_at: str | None
    files_downloaded: int
    error: str


@dataclass
class DueTask:
    """A login + its accounts, packaged for the agent worker."""

    login: Login
    accounts: list[Account]
    kind: str


_SCHEMA = """
CREATE TABLE IF NOT EXISTS login (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_slug TEXT NOT NULL,
    nickname TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending_login',
    storage_state_encrypted TEXT NOT NULL DEFAULT '',
    cookies_captured_at TEXT,
    cadence TEXT NOT NULL DEFAULT 'daily',
    preferred_run_hour_local INTEGER NOT NULL DEFAULT 6,
    next_run_at TEXT,
    last_run_at TEXT,
    last_success_at TEXT,
    last_failure_reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    UNIQUE(institution_slug, nickname)
);

CREATE TABLE IF NOT EXISTS account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login_id INTEGER NOT NULL REFERENCES login(id) ON DELETE CASCADE,
    detected_account_name TEXT NOT NULL DEFAULT '',
    activity_url_encrypted TEXT NOT NULL DEFAULT '',
    flow TEXT NOT NULL DEFAULT 'deposit',
    storage_uri TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_success_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_account_login ON account(login_id);

CREATE TABLE IF NOT EXISTS run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login_id INTEGER NOT NULL REFERENCES login(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    files_downloaded INTEGER NOT NULL DEFAULT 0,
    error TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_run_login ON run(login_id);
"""


class AgentStore:
    """Thin wrapper over an SQLite vault.

    Cheap to instantiate; opens a fresh connection per call. Concurrency
    on a single-user desktop is low so this is fine.
    """

    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
            self._migrate_schema(conn)

    def _migrate_schema(self, conn: sqlite3.Connection) -> None:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(account)").fetchall()}
        if "richtato_account_id" not in columns:
            conn.execute("ALTER TABLE account ADD COLUMN richtato_account_id INTEGER")

    # -------- Logins ------------------------------------------------------

    def add_login(
        self,
        *,
        institution_slug: str,
        nickname: str = "",
        cadence: str = "daily",
        preferred_run_hour_local: int = 6,
    ) -> Login:
        """Create a new login row in ``pending_login`` status."""
        if cadence not in CADENCES:
            raise ValueError(f"cadence must be one of {CADENCES}, got {cadence!r}")
        if not 0 <= preferred_run_hour_local <= 23:
            raise ValueError("preferred_run_hour_local must be 0..23")
        now = _utc_now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO login (
                    institution_slug, nickname, cadence,
                    preferred_run_hour_local, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (institution_slug, nickname, cadence, preferred_run_hour_local, now),
            )
            login_id = cursor.lastrowid
        return self.get_login(login_id)  # type: ignore[return-value]

    def get_login(self, login_id: int) -> Login | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM login WHERE id = ?", (login_id,)).fetchone()
        return _row_to_login(row) if row else None

    def list_logins(self) -> list[Login]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM login ORDER BY id").fetchall()
        return [_row_to_login(row) for row in rows]

    def set_storage_state(self, login_id: int, storage_state_json: str) -> None:
        """Encrypt and persist the Playwright storage_state for a login."""
        encrypted = encrypt_text(storage_state_json) if storage_state_json else ""
        now = _utc_now_iso() if storage_state_json else None
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE login
                SET storage_state_encrypted = ?, cookies_captured_at = ?, status = ?
                WHERE id = ?
                """,
                (encrypted, now, "active" if storage_state_json else "pending_login", login_id),
            )

    def set_login_status(
        self,
        login_id: int,
        status: str,
        *,
        last_failure_reason: str | None = None,
    ) -> None:
        if status not in LOGIN_STATUSES:
            raise ValueError(f"status must be one of {LOGIN_STATUSES}, got {status!r}")
        with self._connect() as conn:
            if last_failure_reason is None:
                conn.execute("UPDATE login SET status = ? WHERE id = ?", (status, login_id))
            else:
                conn.execute(
                    "UPDATE login SET status = ?, last_failure_reason = ? WHERE id = ?",
                    (status, last_failure_reason, login_id),
                )

    def update_login_schedule(
        self,
        login_id: int,
        *,
        cadence: str | None = None,
        preferred_run_hour_local: int | None = None,
        next_run_at: str | None = None,
    ) -> None:
        updates: list[str] = []
        params: list[Any] = []
        if cadence is not None:
            if cadence not in CADENCES:
                raise ValueError(f"cadence must be one of {CADENCES}")
            updates.append("cadence = ?")
            params.append(cadence)
        if preferred_run_hour_local is not None:
            if not 0 <= preferred_run_hour_local <= 23:
                raise ValueError("preferred_run_hour_local must be 0..23")
            updates.append("preferred_run_hour_local = ?")
            params.append(preferred_run_hour_local)
        if next_run_at is not None:
            updates.append("next_run_at = ?")
            params.append(next_run_at)
        if not updates:
            return
        params.append(login_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE login SET {', '.join(updates)} WHERE id = ?", params)

    def record_login_outcome(
        self,
        login_id: int,
        *,
        succeeded: bool,
        failure_reason: str = "",
    ) -> None:
        """Update last_run_at / last_success_at / next_run_at after a run."""
        now = _utc_now_iso()
        with self._connect() as conn:
            login = conn.execute("SELECT * FROM login WHERE id = ?", (login_id,)).fetchone()
            if login is None:
                return
            next_run = _compute_next_run_at(login["cadence"], login["preferred_run_hour_local"])
            if succeeded:
                conn.execute(
                    """
                    UPDATE login
                    SET last_run_at = ?, last_success_at = ?, next_run_at = ?,
                        last_failure_reason = ''
                    WHERE id = ?
                    """,
                    (now, now, next_run, login_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE login
                    SET last_run_at = ?, next_run_at = ?, last_failure_reason = ?
                    WHERE id = ?
                    """,
                    (now, next_run, failure_reason or "", login_id),
                )

    def delete_login(self, login_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM login WHERE id = ?", (login_id,))

    # -------- Accounts ----------------------------------------------------

    def add_account(
        self,
        *,
        login_id: int,
        storage_uri: str = "",
        activity_url: str = "",
        flow: str = "deposit",
        detected_account_name: str = "",
        richtato_account_id: int | None = None,
    ) -> Account:
        if flow not in ACCOUNT_FLOWS:
            raise ValueError(f"flow must be one of {ACCOUNT_FLOWS}, got {flow!r}")
        if flow != "investment_balance" and not storage_uri:
            raise ValueError("storage_uri is required")
        if flow == "investment_balance" and not richtato_account_id:
            raise ValueError("richtato_account_id is required for investment_balance flow")
        encrypted_url = encrypt_text(activity_url) if activity_url else ""
        now = _utc_now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO account (
                    login_id, detected_account_name, activity_url_encrypted,
                    flow, storage_uri, richtato_account_id, enabled, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    login_id,
                    detected_account_name,
                    encrypted_url,
                    flow,
                    storage_uri,
                    richtato_account_id,
                    now,
                ),
            )
            account_id = cursor.lastrowid
        return self.get_account(account_id)  # type: ignore[return-value]

    def get_account(self, account_id: int) -> Account | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM account WHERE id = ?", (account_id,)).fetchone()
        return _row_to_account(row) if row else None

    def list_accounts(self, login_id: int | None = None) -> list[Account]:
        with self._connect() as conn:
            if login_id is None:
                rows = conn.execute("SELECT * FROM account ORDER BY id").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM account WHERE login_id = ? ORDER BY id",
                    (login_id,),
                ).fetchall()
        return [_row_to_account(row) for row in rows]

    def update_account(
        self,
        account_id: int,
        *,
        activity_url: str | None = None,
        flow: str | None = None,
        storage_uri: str | None = None,
        detected_account_name: str | None = None,
        richtato_account_id: int | None = None,
        enabled: bool | None = None,
    ) -> None:
        updates: list[str] = []
        params: list[Any] = []
        if activity_url is not None:
            updates.append("activity_url_encrypted = ?")
            params.append(encrypt_text(activity_url) if activity_url else "")
        if flow is not None:
            if flow not in ACCOUNT_FLOWS:
                raise ValueError(f"flow must be one of {ACCOUNT_FLOWS}")
            updates.append("flow = ?")
            params.append(flow)
        if storage_uri is not None:
            updates.append("storage_uri = ?")
            params.append(storage_uri)
        if detected_account_name is not None:
            updates.append("detected_account_name = ?")
            params.append(detected_account_name)
        if richtato_account_id is not None:
            updates.append("richtato_account_id = ?")
            params.append(richtato_account_id)
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        if not updates:
            return
        params.append(account_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE account SET {', '.join(updates)} WHERE id = ?", params)

    def mark_account_success(self, account_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE account SET last_success_at = ? WHERE id = ?",
                (_utc_now_iso(), account_id),
            )

    def delete_account(self, account_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM account WHERE id = ?", (account_id,))

    # -------- Runs --------------------------------------------------------

    def start_run(self, login_id: int, kind: str) -> Run:
        if kind not in RUN_KINDS:
            raise ValueError(f"kind must be one of {RUN_KINDS}")
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO run (login_id, kind, status, started_at) VALUES (?, ?, 'running', ?)",
                (login_id, kind, _utc_now_iso()),
            )
            run_id = cursor.lastrowid
        return self.get_run(run_id)  # type: ignore[return-value]

    def finish_run(
        self,
        run_id: int,
        *,
        status: str,
        files_downloaded: int = 0,
        error: str = "",
    ) -> None:
        if status not in RUN_STATUSES:
            raise ValueError(f"status must be one of {RUN_STATUSES}, got {status!r}")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE run
                SET status = ?, finished_at = ?, files_downloaded = ?, error = ?
                WHERE id = ?
                """,
                (
                    status,
                    _utc_now_iso(),
                    files_downloaded,
                    error,
                    run_id,
                ),
            )

    def get_run(self, run_id: int) -> Run | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM run WHERE id = ?", (run_id,)).fetchone()
        return _row_to_run(row) if row else None

    def list_runs(self, login_id: int | None = None, limit: int = 25) -> list[Run]:
        with self._connect() as conn:
            if login_id is None:
                rows = conn.execute(
                    "SELECT * FROM run ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM run WHERE login_id = ? ORDER BY id DESC LIMIT ?",
                    (login_id, limit),
                ).fetchall()
        return [_row_to_run(row) for row in rows]

    # -------- Scheduling -------------------------------------------------

    def due_logins(self, *, now: datetime | None = None) -> list[Login]:
        """Return logins whose ``next_run_at`` has elapsed and are active."""
        moment = (now or datetime.now(timezone.utc)).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM login
                WHERE status = 'active'
                  AND cadence != 'manual'
                  AND (next_run_at IS NULL OR next_run_at <= ?)
                ORDER BY id
                """,
                (moment,),
            ).fetchall()
        return [_row_to_login(row) for row in rows]


# ---------- Helpers ----------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_next_run_at(cadence: str, hour: int) -> str | None:
    """Compute the next due timestamp from a cadence + preferred local hour."""
    if cadence == "manual":
        return None
    now = datetime.now(timezone.utc).astimezone()
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if cadence == "daily":
        if target <= now:
            target = target + timedelta(days=1)
    elif cadence == "weekly":
        target = target + timedelta(days=7) if target <= now else target + timedelta(days=6)
    elif cadence == "monthly":
        target = _add_months(target, 1) if target <= now else _add_months(target, 0)
    return target.astimezone(timezone.utc).isoformat()


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month)


def _row_to_login(row: sqlite3.Row) -> Login:
    return Login(
        id=row["id"],
        institution_slug=row["institution_slug"],
        nickname=row["nickname"],
        status=row["status"],
        cookies_captured_at=row["cookies_captured_at"],
        cadence=row["cadence"],
        preferred_run_hour_local=row["preferred_run_hour_local"],
        next_run_at=row["next_run_at"],
        last_run_at=row["last_run_at"],
        last_success_at=row["last_success_at"],
        last_failure_reason=row["last_failure_reason"],
        storage_state_encrypted=row["storage_state_encrypted"],
        created_at=row["created_at"],
    )


def _row_to_account(row: sqlite3.Row) -> Account:
    keys = row.keys()
    richtato_account_id = row["richtato_account_id"] if "richtato_account_id" in keys else None
    return Account(
        id=row["id"],
        login_id=row["login_id"],
        detected_account_name=row["detected_account_name"],
        activity_url_encrypted=row["activity_url_encrypted"],
        flow=row["flow"],
        storage_uri=row["storage_uri"],
        richtato_account_id=richtato_account_id,
        enabled=bool(row["enabled"]),
        last_success_at=row["last_success_at"],
        created_at=row["created_at"],
    )


def _row_to_run(row: sqlite3.Row) -> Run:
    return Run(
        id=row["id"],
        login_id=row["login_id"],
        kind=row["kind"],
        status=row["status"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        files_downloaded=row["files_downloaded"],
        error=row["error"],
    )


def export_to_dict(store: AgentStore) -> dict[str, Any]:
    """Export the agent vault to a plain JSON-able dict for backup or migration."""
    return {
        "logins": [
            {
                "id": login.id,
                "institution_slug": login.institution_slug,
                "nickname": login.nickname,
                "cadence": login.cadence,
                "preferred_run_hour_local": login.preferred_run_hour_local,
                "status": login.status,
                # NOTE: encrypted blobs are exported as-is; restoring requires
                # the same BANK_AGENT_FERNET_KEY.
                "storage_state_encrypted": login.storage_state_encrypted,
                "cookies_captured_at": login.cookies_captured_at,
            }
            for login in store.list_logins()
        ],
        "accounts": [
            {
                "id": account.id,
                "login_id": account.login_id,
                "detected_account_name": account.detected_account_name,
                "activity_url_encrypted": account.activity_url_encrypted,
                "flow": account.flow,
                "storage_uri": account.storage_uri,
                "richtato_account_id": account.richtato_account_id,
                "enabled": account.enabled,
            }
            for account in store.list_accounts()
        ],
    }


def import_from_dict(store: AgentStore, payload: dict[str, Any]) -> tuple[int, int]:
    """Import logins + accounts from a previously exported dict.

    Accepts two payload shapes:

    * Self-export (``storage_state_encrypted``/``activity_url_encrypted``)
      — the encrypted blobs are written verbatim. Requires the same
      ``BANK_AGENT_FERNET_KEY`` that produced the export.
    * Backend migration (``storage_state_plaintext``/``activity_url_plaintext``)
      — the agent re-encrypts the plaintext with its own key. Used when
      copying state out of the legacy ``apps.bank_sync`` vault.

    Returns ``(logins_added, accounts_added)``. Pre-existing rows with the
    same ``(institution_slug, nickname)`` are skipped.
    """
    logins_added = 0
    accounts_added = 0
    existing_keys = {(login.institution_slug, login.nickname) for login in store.list_logins()}

    for login_payload in payload.get("logins", []):
        key = (login_payload["institution_slug"], login_payload.get("nickname", ""))
        if key in existing_keys:
            continue
        login = store.add_login(
            institution_slug=login_payload["institution_slug"],
            nickname=login_payload.get("nickname", ""),
            cadence=login_payload.get("cadence", "daily"),
            preferred_run_hour_local=login_payload.get("preferred_run_hour_local", 6),
        )

        plaintext = login_payload.get("storage_state_plaintext")
        if plaintext:
            store.set_storage_state(login.id, plaintext)
        else:
            encrypted_blob = login_payload.get("storage_state_encrypted") or ""
            if encrypted_blob:
                with store._connect() as conn:  # noqa: SLF001 - one-off migration use
                    conn.execute(
                        """
                        UPDATE login
                        SET storage_state_encrypted = ?, cookies_captured_at = ?, status = 'active'
                        WHERE id = ?
                        """,
                        (encrypted_blob, login_payload.get("cookies_captured_at"), login.id),
                    )
        logins_added += 1

        for account_payload in payload.get("accounts", []):
            if account_payload.get("login_id") != login_payload.get("id"):
                continue
            url_plaintext = account_payload.get("activity_url_plaintext")
            url_encrypted = account_payload.get("activity_url_encrypted") or ""
            store.add_account(
                login_id=login.id,
                storage_uri=account_payload.get("storage_uri", ""),
                activity_url=url_plaintext or "",
                flow=account_payload.get("flow", "deposit"),
                detected_account_name=account_payload.get("detected_account_name", ""),
                richtato_account_id=account_payload.get("richtato_account_id"),
            )
            if not url_plaintext and url_encrypted:
                with store._connect() as conn:  # noqa: SLF001
                    conn.execute(
                        "UPDATE account SET activity_url_encrypted = ? WHERE id = (SELECT MAX(id) FROM account)",
                        (url_encrypted,),
                    )
            accounts_added += 1

    return logins_added, accounts_added


def dumps(payload: dict[str, Any]) -> str:
    """JSON-encode an export payload deterministically."""
    return json.dumps(payload, indent=2, sort_keys=True)
