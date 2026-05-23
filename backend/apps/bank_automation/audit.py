"""Lightweight audit logging for bank automation actions.

Phase 2 ships an append-only structured log written through ``loguru``
under the ``bank_automation.audit`` channel. Operators can ship the log
file to their SIEM of choice. A future phase can introduce a database
model for in-app review without changing the call sites here.

The log is intentionally narrow: never include cookies, activity URLs,
or any value that would defeat encryption-at-rest. Use stable IDs and
short summaries instead.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

EVENT_SESSION_CAPTURED = "session_captured"
EVENT_SESSION_REFRESHED = "session_refreshed"
EVENT_CONNECTION_DISABLED = "connection_disabled"
EVENT_CONNECTION_DELETED = "connection_deleted"
EVENT_CONNECTION_UPDATED = "connection_updated"
EVENT_MANUAL_RUN_REQUESTED = "manual_run_requested"
EVENT_RUN_COMPLETED = "run_completed"
EVENT_RUN_FAILED = "run_failed"
EVENT_REAUTH_REQUIRED = "reauth_required"


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
    connection_id: int | None = None,
    summary: str = "",
    request=None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record one audit event.

    Always non-fatal: if structured logging fails for any reason we still
    let the calling request succeed. Audit log is for forensics, not for
    blocking writes.
    """

    try:
        payload: dict[str, Any] = {
            "event": event,
            "user_id": user_id,
            "connection_id": connection_id,
            "summary": summary,
            "ip_address": _client_ip(request),
            "user_agent": _user_agent(request),
            "metadata": metadata or {},
        }
        logger.bind(audit_channel="bank_automation").info(
            "bank_automation.audit {event} user_id={user_id} conn_id={connection_id} ip={ip} {summary}",
            event=event,
            user_id=user_id,
            connection_id=connection_id,
            ip=payload["ip_address"] or "-",
            summary=summary or "",
            **{"audit_payload": payload},
        )
    except Exception:  # pragma: no cover - best-effort logging
        logger.exception("Failed to record bank automation audit event {}", event)
