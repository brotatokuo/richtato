"""Lightweight audit logging for bank sync actions.

Append-only structured log written through ``loguru`` under the
``bank_sync.audit`` channel. Operators can ship the log to their SIEM of
choice. A future phase can introduce a database model for in-app review
without changing the call sites here.

The log is intentionally narrow: never include cookies, activity URLs, or
any value that would defeat encryption-at-rest. Use stable IDs and short
summaries instead.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

EVENT_LOGIN_CREATED = "login_created"
EVENT_LOGIN_UPDATED = "login_updated"
EVENT_LOGIN_DELETED = "login_deleted"
EVENT_INTERACTIVE_LOGIN_STARTED = "interactive_login_started"
EVENT_SESSION_CAPTURED = "session_captured"
EVENT_MANUAL_SYNC_REQUESTED = "manual_sync_requested"
EVENT_REAUTH_REQUIRED = "reauth_required"
EVENT_SYNC_SUCCEEDED = "sync_succeeded"
EVENT_SYNC_FAILED = "sync_failed"


def _client_ip(request) -> str:
    if request is None:
        return ""
    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "") if hasattr(request, "META") else ""
    if fwd:
        return fwd.split(",")[0].strip()
    return getattr(request, "META", {}).get("REMOTE_ADDR", "") or ""


def _user_agent(request) -> str:
    if request is None:
        return ""
    return getattr(request, "META", {}).get("HTTP_USER_AGENT", "")[:255]


def audit(
    event: str,
    *,
    user_id: int | None = None,
    login_id: int | None = None,
    summary: str = "",
    request=None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record one audit event. Best-effort; never raises into the caller."""

    try:
        payload: dict[str, Any] = {
            "event": event,
            "user_id": user_id,
            "login_id": login_id,
            "summary": summary,
            "ip_address": _client_ip(request),
            "user_agent": _user_agent(request),
            "metadata": metadata or {},
        }
        logger.bind(audit_channel="bank_sync").info(
            "bank_sync.audit {event} user_id={user_id} login_id={login_id} ip={ip} {summary}",
            event=event,
            user_id=user_id,
            login_id=login_id,
            ip=payload["ip_address"] or "-",
            summary=summary or "",
            **{"audit_payload": payload},
        )
    except Exception:  # pragma: no cover - best-effort logging
        logger.exception("Failed to record bank_sync audit event {}", event)
