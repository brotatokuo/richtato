"""Tests for the next_run_at recompute service.

The cadence math is the easiest place for off-by-one errors that produce
hard-to-debug schedule drift, so each branch (manual / daily / weekly /
biweekly / monthly) has explicit timezone-aware coverage.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from apps.bank_automation.models import BankConnection
from apps.bank_automation.services.scheduling import compute_next_run_at, reschedule
from apps.financial_account.models import FinancialInstitution
from apps.richtato_user.models import User

_USER_COUNTER = {"n": 0}


def _make_user(tz_name: str = "America/Los_Angeles") -> User:
    _USER_COUNTER["n"] += 1
    user = User.objects.create_user(username=f"user_{tz_name.replace('/', '_')}_{_USER_COUNTER['n']}", password="x")
    # UserPreference is auto-created via post_save signal; just update timezone.
    user.preferences.timezone = tz_name
    user.preferences.save()
    return user


def _make_connection(user: User, **overrides) -> BankConnection:
    institution, _ = FinancialInstitution.objects.get_or_create(name="Bank of America", defaults={"slug": "bofa"})
    defaults = {
        "user": user,
        "institution": institution,
        "login_id": "test_login",
        "cadence": "daily",
        "preferred_run_hour_local": 6,
    }
    defaults.update(overrides)
    return BankConnection.objects.create(**defaults)


@pytest.mark.django_db
class TestComputeNextRunAt:
    """Cadence-by-cadence schedule math."""

    def test_manual_returns_none(self):
        user = _make_user()
        connection = _make_connection(user, cadence="manual")
        assert compute_next_run_at(connection) is None

    def test_daily_picks_today_when_before_preferred_hour(self):
        user = _make_user("America/Los_Angeles")
        connection = _make_connection(user, cadence="daily", preferred_run_hour_local=6)
        # 03:00 LA on 2026-06-01 -> next run should be 06:00 LA same day
        fake_now_utc = datetime(2026, 6, 1, 10, 0, tzinfo=ZoneInfo("UTC"))
        with patch.object(timezone, "now", return_value=fake_now_utc):
            result = compute_next_run_at(connection)
        assert result is not None
        local = result.astimezone(ZoneInfo("America/Los_Angeles"))
        assert (local.year, local.month, local.day, local.hour) == (2026, 6, 1, 6)

    def test_daily_rolls_to_tomorrow_after_preferred_hour(self):
        user = _make_user("America/Los_Angeles")
        connection = _make_connection(user, cadence="daily", preferred_run_hour_local=6)
        # 09:00 LA on 2026-06-01 -> already past 06:00, run at 06:00 tomorrow
        fake_now_utc = datetime(2026, 6, 1, 16, 0, tzinfo=ZoneInfo("UTC"))
        with patch.object(timezone, "now", return_value=fake_now_utc):
            result = compute_next_run_at(connection)
        local = result.astimezone(ZoneInfo("America/Los_Angeles"))
        assert (local.year, local.month, local.day, local.hour) == (2026, 6, 2, 6)

    def test_weekly_with_no_history_uses_daily_heuristic(self):
        user = _make_user("America/Los_Angeles")
        connection = _make_connection(user, cadence="weekly", preferred_run_hour_local=6)
        fake_now_utc = datetime(2026, 6, 1, 10, 0, tzinfo=ZoneInfo("UTC"))
        with patch.object(timezone, "now", return_value=fake_now_utc):
            result = compute_next_run_at(connection)
        local = result.astimezone(ZoneInfo("America/Los_Angeles"))
        assert local.hour == 6

    def test_weekly_with_last_success_advances_seven_days(self):
        user = _make_user("America/Los_Angeles")
        last_success = datetime(2026, 6, 1, 13, 0, tzinfo=ZoneInfo("UTC"))  # 06:00 LA
        connection = _make_connection(
            user,
            cadence="weekly",
            preferred_run_hour_local=6,
            last_success_at=last_success,
        )
        fake_now_utc = datetime(2026, 6, 2, 10, 0, tzinfo=ZoneInfo("UTC"))
        with patch.object(timezone, "now", return_value=fake_now_utc):
            result = compute_next_run_at(connection)
        local = result.astimezone(ZoneInfo("America/Los_Angeles"))
        assert (local.year, local.month, local.day, local.hour) == (2026, 6, 8, 6)

    def test_biweekly_with_last_success_advances_fourteen_days(self):
        user = _make_user("America/Los_Angeles")
        last_success = datetime(2026, 6, 1, 13, 0, tzinfo=ZoneInfo("UTC"))
        connection = _make_connection(
            user,
            cadence="biweekly",
            preferred_run_hour_local=6,
            last_success_at=last_success,
        )
        fake_now_utc = datetime(2026, 6, 2, 10, 0, tzinfo=ZoneInfo("UTC"))
        with patch.object(timezone, "now", return_value=fake_now_utc):
            result = compute_next_run_at(connection)
        local = result.astimezone(ZoneInfo("America/Los_Angeles"))
        assert (local.year, local.month, local.day, local.hour) == (2026, 6, 15, 6)

    def test_monthly_with_last_success_advances_one_month(self):
        user = _make_user("America/Los_Angeles")
        last_success = datetime(2026, 6, 1, 13, 0, tzinfo=ZoneInfo("UTC"))
        connection = _make_connection(
            user,
            cadence="monthly",
            preferred_run_hour_local=6,
            last_success_at=last_success,
        )
        fake_now_utc = datetime(2026, 6, 2, 10, 0, tzinfo=ZoneInfo("UTC"))
        with patch.object(timezone, "now", return_value=fake_now_utc):
            result = compute_next_run_at(connection)
        local = result.astimezone(ZoneInfo("America/Los_Angeles"))
        assert (local.year, local.month, local.day, local.hour) == (2026, 7, 1, 6)

    def test_monthly_caps_to_end_of_short_month(self):
        """Last-day-of-31-day month should snap to 28/29/30 in shorter months."""

        user = _make_user("UTC")
        last_success = datetime(2026, 1, 31, 6, 0, tzinfo=ZoneInfo("UTC"))
        connection = _make_connection(
            user,
            cadence="monthly",
            preferred_run_hour_local=6,
            last_success_at=last_success,
        )
        fake_now_utc = datetime(2026, 2, 1, 0, 0, tzinfo=ZoneInfo("UTC"))
        with patch.object(timezone, "now", return_value=fake_now_utc):
            result = compute_next_run_at(connection)
        # Feb 2026 has 28 days
        assert result.month == 2
        assert result.day == 28

    def test_reschedule_persists_and_returns_connection(self):
        user = _make_user("UTC")
        connection = _make_connection(user, cadence="daily", preferred_run_hour_local=6)
        result = reschedule(connection)
        assert result.next_run_at is not None
        connection.refresh_from_db()
        assert connection.next_run_at == result.next_run_at

    def test_reschedule_manual_clears_next_run_at(self):
        user = _make_user("UTC")
        connection = _make_connection(user, cadence="manual")
        # Pre-populate to ensure it's actually being cleared.
        connection.next_run_at = timezone.now()
        connection.save()
        reschedule(connection)
        connection.refresh_from_db()
        assert connection.next_run_at is None
