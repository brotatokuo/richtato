"""Cadence-driven scheduling for ``BankConnection.next_run_at``.

The scheduler model is "single source of truth via ``next_run_at``": every
time we run a connection (or the user changes its cadence), we recompute
``next_run_at`` and the worker just polls for connections whose value is in
the past.

All schedule math is done in the user's local timezone so a 6 AM preferred
hour means 6 AM in their wall clock, not UTC.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, time, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

if TYPE_CHECKING:
    from apps.bank_automation.models import BankConnection

# Spread runs across the configured hour to avoid every multi-tenant
# connection hammering the same bank at the top of the hour. Phase 2: a
# stable per-connection minute (0..MAX_JITTER_MINUTES-1) keyed off the
# connection ID so each run lands at the same minute every cadence cycle.
MAX_JITTER_MINUTES = 55


def _connection_jitter_minutes(connection: BankConnection) -> int:
    """Deterministic 0..MAX_JITTER_MINUTES-1 offset for one connection.

    Hashing on connection id (rather than user id) means two connections
    under the same user still pick different minutes, which slightly
    smooths the load when the user has e.g. BofA + Chase running at 6 AM.
    """

    if connection.pk is None:
        return 0
    digest = hashlib.sha256(str(connection.pk).encode("utf-8")).digest()
    return int.from_bytes(digest[:2], "big") % MAX_JITTER_MINUTES


def _user_timezone(user) -> ZoneInfo:
    """Resolve the user's timezone, falling back to UTC if unavailable."""

    pref = getattr(user, "preferences", None)
    tz_name = getattr(pref, "timezone", None) or "UTC"
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _at_hour_in_tz(local_date, hour: int, tz: ZoneInfo, *, minute: int = 0) -> datetime:
    """Combine a local date with a local hour and return a timezone-aware datetime."""

    local_dt = datetime.combine(local_date, time(hour=hour, minute=minute))
    return local_dt.replace(tzinfo=tz)


def _add_months(local_dt: datetime, months: int) -> datetime:
    """Add ``months`` calendar months to a tz-aware datetime, capping at end-of-month.

    Avoids dateutil to keep the dependency footprint minimal.
    """

    month_zero_indexed = local_dt.month - 1 + months
    new_year = local_dt.year + month_zero_indexed // 12
    new_month = month_zero_indexed % 12 + 1
    # Cap day to the last day of the new month.
    if new_month == 12:
        next_month_first = datetime(new_year + 1, 1, 1, tzinfo=local_dt.tzinfo)
    else:
        next_month_first = datetime(new_year, new_month + 1, 1, tzinfo=local_dt.tzinfo)
    last_day_of_new_month = (next_month_first - timedelta(days=1)).day
    new_day = min(local_dt.day, last_day_of_new_month)
    return local_dt.replace(year=new_year, month=new_month, day=new_day)


def compute_next_run_at(
    connection: BankConnection,
    after: datetime | None = None,
) -> datetime | None:
    """Return the next scheduled run time for ``connection``.

    Returns ``None`` for the ``manual`` cadence (only runs via explicit
    "Sync now"). For all other cadences, returns the next preferred-hour
    occurrence in the user's local timezone, strictly after ``after``
    (default: now).
    """

    if connection.cadence == "manual":
        return None

    tz = _user_timezone(connection.user)
    now_local = (after or timezone.now()).astimezone(tz)

    jitter = _connection_jitter_minutes(connection)
    target_today = _at_hour_in_tz(now_local.date(), connection.preferred_run_hour_local, tz, minute=jitter)

    if connection.cadence == "daily":
        candidate = target_today if target_today > now_local else target_today + timedelta(days=1)
        return candidate.astimezone(UTC)

    last_success = connection.last_success_at
    if connection.cadence == "weekly":
        delta = timedelta(days=7)
    elif connection.cadence == "biweekly":
        delta = timedelta(days=14)
    elif connection.cadence == "monthly":
        delta = None  # handled below
    else:  # pragma: no cover — defensive
        return None

    if connection.cadence in {"weekly", "biweekly"}:
        if last_success is None:
            # First run uses the same-day-or-tomorrow heuristic as daily so
            # users see something happen quickly after connecting.
            candidate = target_today if target_today > now_local else target_today + timedelta(days=1)
        else:
            base_local = last_success.astimezone(tz)
            anchor = _at_hour_in_tz(
                base_local.date(),
                connection.preferred_run_hour_local,
                tz,
                minute=jitter,
            )
            candidate = anchor + delta
            while candidate <= now_local:
                candidate += delta
        return candidate.astimezone(UTC)

    # Monthly
    if last_success is None:
        candidate = target_today if target_today > now_local else target_today + timedelta(days=1)
    else:
        base_local = last_success.astimezone(tz)
        anchor = _at_hour_in_tz(
            base_local.date(),
            connection.preferred_run_hour_local,
            tz,
            minute=jitter,
        )
        candidate = _add_months(anchor, 1)
        while candidate <= now_local:
            candidate = _add_months(candidate, 1)
    return candidate.astimezone(UTC)


def reschedule(connection: BankConnection, *, save: bool = True) -> BankConnection:
    """Recompute ``connection.next_run_at`` and (optionally) save."""

    connection.next_run_at = compute_next_run_at(connection)
    if save:
        connection.save(update_fields=["next_run_at", "updated_at"])
    return connection
