"""Cadence-driven scheduling for ``BankLogin.next_run_at``.

Single source of truth via ``next_run_at``: every time we run a login (or
the user changes its cadence) we recompute ``next_run_at`` and the agent
just polls for logins whose value is in the past.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, time, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

if TYPE_CHECKING:
    from apps.bank_sync.models import BankLogin

# Spread runs across the configured hour so a multi-tenant deployment does
# not hammer the same bank at the top of the hour.
MAX_JITTER_MINUTES = 55


def _login_jitter_minutes(login: BankLogin) -> int:
    if login.pk is None:
        return 0
    digest = hashlib.sha256(str(login.pk).encode("utf-8")).digest()
    return int.from_bytes(digest[:2], "big") % MAX_JITTER_MINUTES


def _user_timezone(user) -> ZoneInfo:
    pref = getattr(user, "preferences", None)
    tz_name = getattr(pref, "timezone", None) or "UTC"
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _at_hour_in_tz(local_date, hour: int, tz: ZoneInfo, *, minute: int = 0) -> datetime:
    local_dt = datetime.combine(local_date, time(hour=hour, minute=minute))
    return local_dt.replace(tzinfo=tz)


def _add_months(local_dt: datetime, months: int) -> datetime:
    month_zero_indexed = local_dt.month - 1 + months
    new_year = local_dt.year + month_zero_indexed // 12
    new_month = month_zero_indexed % 12 + 1
    if new_month == 12:
        next_month_first = datetime(new_year + 1, 1, 1, tzinfo=local_dt.tzinfo)
    else:
        next_month_first = datetime(new_year, new_month + 1, 1, tzinfo=local_dt.tzinfo)
    last_day_of_new_month = (next_month_first - timedelta(days=1)).day
    new_day = min(local_dt.day, last_day_of_new_month)
    return local_dt.replace(year=new_year, month=new_month, day=new_day)


def compute_next_run_at(
    login: BankLogin,
    after: datetime | None = None,
) -> datetime | None:
    """Return the next scheduled run time for ``login`` in UTC.

    ``None`` for ``manual`` cadence (sync only on explicit user action) and
    for non-``active`` statuses.
    """

    if login.status != "active":
        return None
    if login.cadence == "manual":
        return None

    tz = _user_timezone(login.user)
    now_local = (after or timezone.now()).astimezone(tz)
    jitter = _login_jitter_minutes(login)
    target_today = _at_hour_in_tz(now_local.date(), login.preferred_run_hour_local, tz, minute=jitter)

    if login.cadence == "daily":
        candidate = target_today if target_today > now_local else target_today + timedelta(days=1)
        return candidate.astimezone(UTC)

    last_success = login.last_success_at
    if login.cadence == "weekly":
        delta = timedelta(days=7)
    elif login.cadence == "monthly":
        delta = None
    else:  # pragma: no cover - defensive
        return None

    if login.cadence == "weekly":
        if last_success is None:
            candidate = target_today if target_today > now_local else target_today + timedelta(days=1)
        else:
            base_local = last_success.astimezone(tz)
            anchor = _at_hour_in_tz(
                base_local.date(),
                login.preferred_run_hour_local,
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
            login.preferred_run_hour_local,
            tz,
            minute=jitter,
        )
        candidate = _add_months(anchor, 1)
        while candidate <= now_local:
            candidate = _add_months(candidate, 1)
    return candidate.astimezone(UTC)


def reschedule(login: BankLogin, *, save: bool = True) -> BankLogin:
    """Recompute ``login.next_run_at`` and (optionally) save."""

    login.next_run_at = compute_next_run_at(login)
    if save:
        login.save(update_fields=["next_run_at", "updated_at"])
    return login
