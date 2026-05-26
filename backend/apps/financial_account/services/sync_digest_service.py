"""Build daily bank-sync digest content for email notifications."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from html import escape
from pathlib import Path

from django.conf import settings
from django.utils import timezone as django_tz

from apps.financial_account.models import FinancialAccount, StatementFile
from apps.financial_account.services.bank_sync_setup_service import BankSyncSetupService
from apps.richtato_user.models import User

ISSUE_LOGIN_STATUSES = frozenset({"needs_reauth", "error", "pending_login"})
ISSUE_RUN_STATUSES = frozenset({"failed", "partial"})


@dataclass(frozen=True)
class AgentLoginRow:
    id: int
    institution_slug: str
    nickname: str
    status: str
    cadence: str
    last_run_at: str | None
    last_success_at: str | None
    last_failure_reason: str


@dataclass(frozen=True)
class AgentAccountRow:
    id: int
    login_id: int
    detected_account_name: str
    flow: str
    richtato_account_id: int | None
    enabled: bool
    last_success_at: str | None


@dataclass(frozen=True)
class AgentRunRow:
    id: int
    login_id: int
    kind: str
    status: str
    started_at: str
    finished_at: str | None
    files_downloaded: int
    error: str


@dataclass
class AgentSnapshot:
    available: bool
    message: str = ""
    logins: list[AgentLoginRow] = field(default_factory=list)
    accounts: list[AgentAccountRow] = field(default_factory=list)
    runs: list[AgentRunRow] = field(default_factory=list)


@dataclass(frozen=True)
class StatementDigestRow:
    account_name: str
    filename: str
    import_status: str
    imported_count: int
    duplicate_count: int
    invalid_count: int


@dataclass(frozen=True)
class SetupGapRow:
    account_name: str
    issue: str


@dataclass
class SyncDigest:
    user: User
    since: datetime
    agent: AgentSnapshot
    logins: list[AgentLoginRow]
    accounts_by_login: dict[int, list[AgentAccountRow]]
    runs: list[AgentRunRow]
    statements: list[StatementDigestRow]
    setup_gaps: list[SetupGapRow]
    overall_ok: bool

    @property
    def subject(self) -> str:
        status = "All OK" if self.overall_ok else "Needs attention"
        return f"Richtato bank sync — {status}"

    def to_text(self) -> str:
        lines = [
            f"Daily bank sync digest for {self.user.username}",
            f"Period: last {self._period_hours()} hours (since {self._format_dt(self.since)})",
            "",
            self._summary_line(),
            "",
        ]
        lines.extend(self._agent_section_text())
        lines.extend(self._statements_section_text())
        lines.extend(self._setup_gaps_section_text())
        lines.append("")
        lines.append(f"Open Richtato: {settings.FRONTEND_URL}/setup")
        return "\n".join(lines)

    def to_html(self) -> str:
        parts = [
            "<h2>Richtato bank sync digest</h2>",
            f"<p>User: <strong>{escape(self.user.username)}</strong><br>",
            f"Period: last {self._period_hours()} hours (since {escape(self._format_dt(self.since))})</p>",
            f"<p><strong>{escape(self._summary_line())}</strong></p>",
        ]
        parts.append(self._agent_section_html())
        parts.append(self._statements_section_html())
        parts.append(self._setup_gaps_section_html())
        parts.append(f'<p><a href="{escape(settings.FRONTEND_URL)}/setup">Open Setup in Richtato</a></p>')
        return "\n".join(parts)

    def _period_hours(self) -> int:
        delta = django_tz.now() - self.since
        return max(1, int(delta.total_seconds() // 3600))

    def _format_dt(self, value: datetime) -> str:
        return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")

    def _summary_line(self) -> str:
        if not self.agent.available:
            return f"Bank agent: {self.agent.message}"
        if self.overall_ok:
            return "Overall: all monitored bank sync activity looks healthy."
        return "Overall: one or more logins, runs, imports, or setup items need attention."

    def _agent_section_text(self) -> list[str]:
        if not self.agent.available:
            return ["Bank agent", "  " + self.agent.message, ""]
        if not self.logins:
            return ["Bank agent", "  No logins in the local vault for your linked accounts.", ""]

        lines = ["Bank logins"]
        for login in self.logins:
            lines.append(
                f"  • {login.institution_slug}"
                + (f" ({login.nickname})" if login.nickname else "")
                + f" — status={login.status}, cadence={login.cadence}"
            )
            if login.last_success_at:
                lines.append(f"    last success: {login.last_success_at}")
            if login.last_failure_reason:
                lines.append(f"    last failure: {login.last_failure_reason}")
            for account in self.accounts_by_login.get(login.id, []):
                lines.append(
                    f"    - {account.detected_account_name} ({account.flow})"
                    f" enabled={account.enabled}"
                    + (f" last_success={account.last_success_at}" if account.last_success_at else "")
                )
        if self.runs:
            lines.append("")
            lines.append("Recent runs")
            for run in self.runs:
                err = f" — {run.error}" if run.error else ""
                lines.append(
                    f"  • login #{run.login_id} {run.kind} {run.status}"
                    f" files={run.files_downloaded} at {run.started_at}{err}"
                )
        lines.append("")
        return lines

    def _statements_section_text(self) -> list[str]:
        if not self.statements:
            return ["Agent statement imports (24h)", "  None in this period.", ""]
        lines = ["Agent statement imports (24h)"]
        for row in self.statements:
            lines.append(
                f"  • {row.account_name}: {row.filename} — {row.import_status}"
                f" (imported={row.imported_count}, dup={row.duplicate_count}, invalid={row.invalid_count})"
            )
        lines.append("")
        return lines

    def _setup_gaps_section_text(self) -> list[str]:
        if not self.setup_gaps:
            return []
        lines = ["Auto-sync setup gaps"]
        for gap in self.setup_gaps:
            lines.append(f"  • {gap.account_name}: {gap.issue}")
        lines.append("")
        return lines

    def _agent_section_html(self) -> str:
        if not self.agent.available:
            return f"<h3>Bank agent</h3><p>{escape(self.agent.message)}</p>"
        if not self.logins:
            return "<h3>Bank agent</h3><p>No logins in the local vault for your linked accounts.</p>"

        rows = []
        for login in self.logins:
            label = login.institution_slug
            if login.nickname:
                label += f" ({escape(login.nickname)})"
            detail = (
                f"status={escape(login.status)}, cadence={escape(login.cadence)}"
                f"; last success: {escape(login.last_success_at or '—')}"
            )
            if login.last_failure_reason:
                detail += f"; failure: {escape(login.last_failure_reason)}"
            rows.append(f"<li><strong>{escape(label)}</strong> — {detail}</li>")
        html = "<h3>Bank logins</h3><ul>" + "".join(rows) + "</ul>"
        if self.runs:
            run_items = []
            for run in self.runs:
                err = f" — {escape(run.error)}" if run.error else ""
                run_items.append(
                    f"<li>login #{run.login_id} {escape(run.kind)} "
                    f"<strong>{escape(run.status)}</strong> "
                    f"files={run.files_downloaded} at {escape(run.started_at)}{err}</li>"
                )
            html += "<h3>Recent runs</h3><ul>" + "".join(run_items) + "</ul>"
        return html

    def _statements_section_html(self) -> str:
        if not self.statements:
            return "<h3>Agent statement imports (24h)</h3><p>None in this period.</p>"
        items = "".join(
            f"<li><strong>{escape(r.account_name)}</strong>: {escape(r.filename)} — "
            f"{escape(r.import_status)} (imported={r.imported_count})</li>"
            for r in self.statements
        )
        return f"<h3>Agent statement imports (24h)</h3><ul>{items}</ul>"

    def _setup_gaps_section_html(self) -> str:
        if not self.setup_gaps:
            return ""
        items = "".join(
            f"<li><strong>{escape(g.account_name)}</strong>: {escape(g.issue)}</li>" for g in self.setup_gaps
        )
        return f"<h3>Auto-sync setup gaps</h3><ul>{items}</ul>"


class SyncDigestService:
    """Assemble per-user digest payloads from agent.db and Django models."""

    def __init__(
        self,
        *,
        db_path: str | Path | None = None,
        setup_service: BankSyncSetupService | None = None,
    ) -> None:
        self.db_path = Path(db_path or settings.BANK_AGENT_DB_PATH)
        self.setup_service = setup_service or BankSyncSetupService()

    def build_digest_for_user(self, user: User, *, since: datetime) -> SyncDigest:
        account_ids = set(FinancialAccount.objects.filter(user=user, is_active=True).values_list("id", flat=True))
        agent = read_agent_snapshot(self.db_path)
        logins, accounts_by_login, runs = self._filter_agent_for_user(agent, account_ids, since)
        statements = self._statement_rows(user, since)
        setup_gaps = self._setup_gaps(user)
        overall_ok = self._compute_overall_ok(agent, logins, runs, statements, setup_gaps)

        return SyncDigest(
            user=user,
            since=since,
            agent=agent,
            logins=logins,
            accounts_by_login=accounts_by_login,
            runs=runs,
            statements=statements,
            setup_gaps=setup_gaps,
            overall_ok=overall_ok,
        )

    def _filter_agent_for_user(
        self,
        agent: AgentSnapshot,
        account_ids: set[int],
        since: datetime,
    ) -> tuple[list[AgentLoginRow], dict[int, list[AgentAccountRow]], list[AgentRunRow]]:
        if not agent.available:
            return [], {}, []

        login_ids: set[int] = set()
        accounts_by_login: dict[int, list[AgentAccountRow]] = {}
        for account in agent.accounts:
            if account.richtato_account_id is None or account.richtato_account_id not in account_ids:
                continue
            login_ids.add(account.login_id)
            accounts_by_login.setdefault(account.login_id, []).append(account)

        logins = [login for login in agent.logins if login.id in login_ids]
        since_iso = since.isoformat()
        runs = [run for run in agent.runs if run.login_id in login_ids and run.started_at >= since_iso]
        return logins, accounts_by_login, runs

    def _statement_rows(self, user: User, since: datetime) -> list[StatementDigestRow]:
        qs = (
            StatementFile.objects.filter(
                user=user,
                is_deleted=False,
                source="agent_drop",
                updated_at__gte=since,
            )
            .select_related("account")
            .order_by("-updated_at")
        )
        return [
            StatementDigestRow(
                account_name=sf.account.name,
                filename=sf.original_filename,
                import_status=sf.import_status,
                imported_count=sf.imported_count,
                duplicate_count=sf.duplicate_count,
                invalid_count=sf.invalid_count,
            )
            for sf in qs
        ]

    def _setup_gaps(self, user: User) -> list[SetupGapRow]:
        payload = self.setup_service.build_for_user(user)
        gaps: list[SetupGapRow] = []
        for row in payload["accounts"]:
            if row["sync_mode"] != "auto":
                continue
            if row.get("needs_storage_for_auto") and not row.get("has_storage_uri"):
                gaps.append(SetupGapRow(account_name=row["name"], issue="missing storage folder (Drive)"))
            if row.get("needs_activity_url_for_auto"):
                gaps.append(SetupGapRow(account_name=row["name"], issue="missing activity URL for bank agent"))
        return gaps

    def _compute_overall_ok(
        self,
        agent: AgentSnapshot,
        logins: list[AgentLoginRow],
        runs: list[AgentRunRow],
        statements: list[StatementDigestRow],
        setup_gaps: list[SetupGapRow],
    ) -> bool:
        if not agent.available:
            return False
        if setup_gaps:
            return False
        if any(login.status in ISSUE_LOGIN_STATUSES for login in logins):
            return False
        if any(login.last_failure_reason.strip() for login in logins):
            return False
        if any(run.status in ISSUE_RUN_STATUSES for run in runs):
            return False
        if any(s.import_status == "failed" for s in statements):
            return False
        return True


def read_agent_snapshot(db_path: Path) -> AgentSnapshot:
    """Read login, account, and run rows from the host bank-agent SQLite vault."""
    if not db_path.is_file():
        return AgentSnapshot(available=False, message=f"Bank agent database not found at {db_path}")

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        return AgentSnapshot(available=False, message=f"Could not open bank agent database: {exc}")

    try:
        logins = [_row_to_login(row) for row in conn.execute("SELECT * FROM login ORDER BY id").fetchall()]
        accounts = [_row_to_account(row) for row in conn.execute("SELECT * FROM account ORDER BY id").fetchall()]
        runs = [_row_to_run(row) for row in conn.execute("SELECT * FROM run ORDER BY id DESC LIMIT 50").fetchall()]
    except sqlite3.Error as exc:
        return AgentSnapshot(available=False, message=f"Could not read bank agent database: {exc}")
    finally:
        conn.close()

    return AgentSnapshot(available=True, logins=logins, accounts=accounts, runs=runs)


def _row_to_login(row: sqlite3.Row) -> AgentLoginRow:
    return AgentLoginRow(
        id=row["id"],
        institution_slug=row["institution_slug"],
        nickname=row["nickname"] or "",
        status=row["status"],
        cadence=row["cadence"],
        last_run_at=row["last_run_at"],
        last_success_at=row["last_success_at"],
        last_failure_reason=row["last_failure_reason"] or "",
    )


def _row_to_account(row: sqlite3.Row) -> AgentAccountRow:
    keys = row.keys()
    richtato_id = row["richtato_account_id"] if "richtato_account_id" in keys else None
    return AgentAccountRow(
        id=row["id"],
        login_id=row["login_id"],
        detected_account_name=row["detected_account_name"] or "",
        flow=row["flow"] or "",
        richtato_account_id=richtato_id,
        enabled=bool(row["enabled"]),
        last_success_at=row["last_success_at"],
    )


def _row_to_run(row: sqlite3.Row) -> AgentRunRow:
    return AgentRunRow(
        id=row["id"],
        login_id=row["login_id"],
        kind=row["kind"],
        status=row["status"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        files_downloaded=row["files_downloaded"] or 0,
        error=row["error"] or "",
    )


def default_since(*, hours: int = 24) -> datetime:
    return django_tz.now() - timedelta(hours=hours)
