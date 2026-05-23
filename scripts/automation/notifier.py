"""Gmail SMTP alert delivery.

A single notifier per run. Failures are buffered and flushed as one aggregated
email at the end of the run so a fully-broken day produces one email, not eight.
"""

from __future__ import annotations

import smtplib
import ssl
import traceback
from dataclasses import dataclass
from email.message import EmailMessage

from loguru import logger

from scripts.automation.config import AutomationConfig
from scripts.automation.errors import ErrorKind
from scripts.automation.state import InstitutionState

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

SUBJECT_BY_KIND: dict[ErrorKind, str] = {
    ErrorKind.SESSION_EXPIRED: "Re-auth needed",
    ErrorKind.DOM_BROKEN: "DOM broken",
    ErrorKind.NO_DOWNLOAD: "No download",
    ErrorKind.IMPORT_REJECTED: "Import failed",
    ErrorKind.CONFIG: "Config error",
    ErrorKind.UNKNOWN: "Unexpected error",
}

REMEDY_BY_KIND: dict[ErrorKind, str] = {
    ErrorKind.SESSION_EXPIRED: (
        "The saved Playwright session for this bank has expired. Re-bootstrap on the Linux desktop:"
    ),
    ErrorKind.DOM_BROKEN: (
        "Navigation through the bank UI failed - the site probably changed. Check the adapter selectors, "
        "then re-bootstrap to refresh the session if needed:"
    ),
    ErrorKind.NO_DOWNLOAD: (
        "The bank page never fired a download event. The export button may have moved or the file is being "
        "rendered inline. Inspect the adapter, then re-bootstrap if cookies are also stale:"
    ),
    ErrorKind.IMPORT_REJECTED: (
        "The downloaded file reached Richtato but the import API rejected it. Check the file format and the "
        "configured account ID for this institution in AUTOMATION_ACCOUNT_IDS."
    ),
    ErrorKind.CONFIG: (
        "Configuration error - check the automation environment variables (AUTOMATION_ACCOUNT_IDS, RICHTATO_RUNNER_TOKEN, etc.)."
    ),
    ErrorKind.UNKNOWN: ("Unexpected failure - see traceback below."),
}


@dataclass
class FailureRecord:
    institution: str
    kind: ErrorKind
    message: str
    last_success: str | None
    consecutive_failures: int
    traceback_excerpt: str | None = None


def _format_remedy_command(institution: str, kind: ErrorKind) -> str | None:
    if kind in {ErrorKind.SESSION_EXPIRED, ErrorKind.DOM_BROKEN, ErrorKind.NO_DOWNLOAD}:
        return (
            f"  cd <repo>\n"
            f"  source .venv-bootstrap/bin/activate\n"
            f"  python scripts/statement_downloader.py {institution} \\\n"
            f"    --storage-state local_data/automation/storage_states/{institution}.json\n"
            f"\n"
            f"After bootstrap, verify with:\n"
            f"  docker compose exec automation python -m scripts.automation.runner --only {institution}"
        )
    return None


def _format_failure_block(failure: FailureRecord) -> str:
    lines: list[str] = []
    lines.append(f"[{failure.institution}] {SUBJECT_BY_KIND[failure.kind]}")
    lines.append(f"  reason: {failure.message}")
    lines.append(f"  consecutive failures: {failure.consecutive_failures}")
    lines.append(f"  last successful run: {failure.last_success or 'never'}")
    lines.append("")
    lines.append(REMEDY_BY_KIND[failure.kind])
    remedy = _format_remedy_command(failure.institution, failure.kind)
    if remedy:
        lines.append("")
        lines.append(remedy)
    if failure.traceback_excerpt:
        lines.append("")
        lines.append("traceback:")
        lines.append(failure.traceback_excerpt)
    return "\n".join(lines)


class Notifier:
    """Buffer failures during a run, then flush a single aggregated email."""

    def __init__(self, config: AutomationConfig) -> None:
        self.config = config
        self._failures: list[FailureRecord] = []
        self._stale: list[tuple[str, InstitutionState]] = []

    def record_failure(
        self,
        institution: str,
        kind: ErrorKind,
        message: str,
        institution_state: InstitutionState,
        exc: BaseException | None = None,
    ) -> None:
        excerpt: str | None = None
        if exc is not None:
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            excerpt = "\n".join(tb.strip().splitlines()[-15:])
        self._failures.append(
            FailureRecord(
                institution=institution,
                kind=kind,
                message=message,
                last_success=institution_state.last_success,
                consecutive_failures=institution_state.consecutive_failures,
                traceback_excerpt=excerpt,
            )
        )

    def record_stale(
        self, institution: str, institution_state: InstitutionState
    ) -> None:
        self._stale.append((institution, institution_state))

    def has_alerts(self) -> bool:
        return bool(self._failures or self._stale)

    def flush(self) -> bool:
        if not self.has_alerts():
            return False

        if not self._can_send():
            logger.warning(
                "Skipping alert email - Gmail credentials not configured "
                "(GMAIL_USER, GMAIL_APP_PASSWORD, ALERT_TO required)"
            )
            return False

        body_sections: list[str] = []
        if self._failures:
            body_sections.append("=== Failures ===")
            body_sections.extend(_format_failure_block(f) for f in self._failures)
        if self._stale:
            body_sections.append("=== Stale institutions ===")
            for institution, entry in self._stale:
                body_sections.append(
                    f"[{institution}] no successful run since {entry.last_success or 'never'}"
                )

        kinds = sorted({f.kind.value for f in self._failures})
        institutions = sorted(
            {f.institution for f in self._failures} | {i for i, _ in self._stale}
        )
        subject_summary = ", ".join(institutions) if institutions else "stale"
        kind_summary = ",".join(kinds) if kinds else "stale"
        subject = f"[Richtato] {kind_summary}: {subject_summary}"

        message = EmailMessage()
        message["From"] = self.config.gmail_user
        message["To"] = self.config.alert_to
        message["Subject"] = subject
        message.set_content("\n\n".join(body_sections))

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as smtp:
                smtp.login(self.config.gmail_user, self.config.gmail_app_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            logger.exception("Failed to send Gmail alert: {}", exc)
            return False

        logger.info(
            "Sent alert email to {} ({} failures, {} stale)",
            self.config.alert_to,
            len(self._failures),
            len(self._stale),
        )
        return True

    def _can_send(self) -> bool:
        return bool(
            self.config.gmail_user
            and self.config.gmail_app_password
            and self.config.alert_to
        )
