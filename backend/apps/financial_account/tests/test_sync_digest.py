"""Tests for daily bank-sync digest email content."""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from apps.core.services.email_service import EmailService
from apps.financial_account.models import FinancialAccount, FinancialInstitution, StatementFile
from apps.financial_account.services.sync_digest_service import (
    SyncDigestService,
    read_agent_snapshot,
)
from apps.richtato_user.models import User, UserPreference


@pytest.fixture
def user(db):
    return User.objects.create_user(username="digestuser", email="digest@test.com", password="x")


@pytest.fixture
def robinhood_institution(db):
    institution, _ = FinancialInstitution.objects.get_or_create(slug="robinhood", defaults={"name": "Robinhood"})
    return institution


def _create_agent_db(path: Path, *, richtato_account_id: int) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE login (
            id INTEGER PRIMARY KEY,
            institution_slug TEXT NOT NULL,
            nickname TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            storage_state_encrypted TEXT NOT NULL DEFAULT '',
            cookies_captured_at TEXT,
            cadence TEXT NOT NULL DEFAULT 'daily',
            preferred_run_hour_local INTEGER NOT NULL DEFAULT 6,
            next_run_at TEXT,
            last_run_at TEXT,
            last_success_at TEXT,
            last_failure_reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE account (
            id INTEGER PRIMARY KEY,
            login_id INTEGER NOT NULL,
            detected_account_name TEXT NOT NULL DEFAULT '',
            activity_url_encrypted TEXT NOT NULL DEFAULT '',
            flow TEXT NOT NULL DEFAULT 'deposit',
            storage_uri TEXT NOT NULL DEFAULT '',
            richtato_account_id INTEGER,
            enabled INTEGER NOT NULL DEFAULT 1,
            last_success_at TEXT,
            created_at TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE run (
            id INTEGER PRIMARY KEY,
            login_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            files_downloaded INTEGER NOT NULL DEFAULT 0,
            error TEXT NOT NULL DEFAULT ''
        );
        """
    )
    conn.execute(
        """
        INSERT INTO login (
            id, institution_slug, nickname, status, cadence,
            last_success_at, last_failure_reason, storage_state_encrypted, created_at
        ) VALUES (1, 'robinhood', 'RH', 'active', 'daily', '2026-05-24T10:00:00+00:00', '', '', '')
        """
    )
    conn.execute(
        """
        INSERT INTO account (
            id, login_id, detected_account_name, flow, richtato_account_id,
            enabled, last_success_at, activity_url_encrypted, storage_uri, created_at
        ) VALUES (1, 1, 'Brokerage', 'investment_balance', ?, 1,
                  '2026-05-24T10:05:00+00:00', '', 'gdrive://folder', '')
        """,
        (richtato_account_id,),
    )
    conn.execute(
        """
        INSERT INTO run (
            id, login_id, kind, status, started_at, finished_at,
            files_downloaded, error
        ) VALUES (1, 1, 'scheduled_download', 'completed', '2026-05-24T11:00:00+00:00',
                  '2026-05-24T11:01:00+00:00', 1, '')
        """
    )
    conn.commit()
    conn.close()


class TestReadAgentSnapshot:
    def test_missing_db(self, tmp_path):
        snapshot = read_agent_snapshot(tmp_path / "missing.db")
        assert snapshot.available is False
        assert "not found" in snapshot.message.lower()

    def test_reads_logins_and_runs(self, tmp_path):
        db_path = tmp_path / "agent.db"
        _create_agent_db(db_path, richtato_account_id=99)
        snapshot = read_agent_snapshot(db_path)
        assert snapshot.available is True
        assert len(snapshot.logins) == 1
        assert snapshot.logins[0].institution_slug == "robinhood"
        assert len(snapshot.accounts) == 1
        assert len(snapshot.runs) == 1


class TestSyncDigestService:
    def test_build_digest_filters_by_user_account(self, user, robinhood_institution, tmp_path):
        account = FinancialAccount.objects.create(
            user=user,
            name="Robinhood Brokerage",
            account_type="investment",
            institution=robinhood_institution,
            sync_mode="manual",
            storage_uri="gdrive://folder",
        )
        db_path = tmp_path / "agent.db"
        _create_agent_db(db_path, richtato_account_id=account.id)

        since = timezone.now() - timedelta(hours=24)
        service = SyncDigestService(db_path=db_path)
        digest = service.build_digest_for_user(user, since=since)

        assert len(digest.logins) == 1
        assert digest.logins[0].institution_slug == "robinhood"
        assert digest.overall_ok is True
        assert "robinhood" in digest.to_text()
        assert "robinhood" in digest.to_html().lower()

    def test_failed_import_marks_not_ok(self, user, robinhood_institution, tmp_path):
        account = FinancialAccount.objects.create(
            user=user,
            name="Robinhood Brokerage",
            account_type="investment",
            institution=robinhood_institution,
            sync_mode="manual",
        )
        db_path = tmp_path / "agent.db"
        _create_agent_db(db_path, richtato_account_id=account.id)

        StatementFile.objects.create(
            user=user,
            account=account,
            institution="robinhood",
            statement_year=2026,
            statement_month=5,
            original_filename="stmt.csv",
            stored_path="gdrive://folder/stmt.csv",
            file_hash="abc123",
            source="agent_drop",
            import_status="failed",
        )

        since = timezone.now() - timedelta(hours=24)
        digest = SyncDigestService(db_path=db_path).build_digest_for_user(user, since=since)
        assert digest.overall_ok is False
        assert "failed" in digest.subject.lower() or "attention" in digest.subject.lower()

    def test_setup_gap_for_auto_without_storage(self, user, robinhood_institution, tmp_path):
        FinancialAccount.objects.create(
            user=user,
            name="Robinhood Checking",
            account_type="checking",
            institution=robinhood_institution,
            sync_mode="auto",
            storage_uri="",
        )
        db_path = tmp_path / "agent.db"
        _create_agent_db(db_path, richtato_account_id=99999)

        since = timezone.now() - timedelta(hours=24)
        digest = SyncDigestService(db_path=db_path).build_digest_for_user(user, since=since)
        assert any("storage" in g.issue.lower() for g in digest.setup_gaps)
        assert digest.overall_ok is False


class TestEmailService:
    @patch("apps.core.services.email_service.requests.post")
    def test_send_success(self, mock_post, settings):
        settings.RESEND_API_KEY = "re_test"
        settings.RESEND_FROM_EMAIL = "Richtato <sync@test.com>"
        mock_post.return_value = MagicMock(status_code=200, text='{"id":"1"}')

        assert EmailService.send(to="user@test.com", subject="Hi", text="Body", html="<p>Body</p>") is True
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs["json"]
        assert payload["to"] == ["user@test.com"]

    def test_send_skipped_when_unconfigured(self, settings):
        settings.RESEND_API_KEY = ""
        settings.RESEND_FROM_EMAIL = ""
        assert EmailService.send(to="user@test.com", subject="Hi", text="Body") is False


class TestSendSyncDigestCommand:
    def test_dry_run_respects_notifications_disabled(self, user, db):
        UserPreference.objects.filter(user=user).update(notifications_enabled=False)
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("send_sync_digest", "--dry-run", "--user-id", str(user.id), stdout=out)
        assert out.getvalue().strip() == "" or "No eligible" in out.getvalue()

    def test_dry_run_includes_enabled_user(self, user, robinhood_institution, tmp_path, settings):
        settings.BANK_AGENT_DB_PATH = str(tmp_path / "agent.db")
        account = FinancialAccount.objects.create(
            user=user,
            name="Robinhood",
            account_type="investment",
            institution=robinhood_institution,
            sync_mode="manual",
        )
        _create_agent_db(Path(settings.BANK_AGENT_DB_PATH), richtato_account_id=account.id)

        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("send_sync_digest", "--dry-run", "--user-id", str(user.id), stdout=out)
        assert "digestuser" in out.getvalue()
        assert "bank sync" in out.getvalue().lower()
