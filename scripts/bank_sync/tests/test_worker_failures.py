"""Tests for worker failure aggregation."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

from scripts.bank_sync.agent_store import AgentStore
from scripts.bank_sync.errors import (
    FailureKind,
    NeedsReauthError,
    NoDownloadError,
    format_failure_reason,
    parse_failure_kind,
)
from scripts.bank_sync.worker import (
    AccountFailure,
    _run_status_for,
    _summarize_account_failures,
    download_login,
)


class TestFailureSummaries:
    def test_summarize_single_account_failure(self):
        summary = _summarize_account_failures(
            [
                AccountFailure(
                    account_id=5,
                    kind=FailureKind.DOM_BROKEN,
                    message="Download button not found",
                )
            ]
        )
        assert summary == format_failure_reason(
            FailureKind.DOM_BROKEN,
            "Account 5: Download button not found",
        )

    def test_run_status_partial_when_some_accounts_succeed(self):
        assert (
            _run_status_for(
                attempted=2,
                succeeded=1,
                needs_reauth=False,
                account_failures=[
                    AccountFailure(
                        account_id=6,
                        kind=FailureKind.NO_DOWNLOAD,
                        message="empty",
                    )
                ],
            )
            == "partial"
        )

    def test_run_status_failed_when_all_accounts_fail(self):
        assert (
            _run_status_for(
                attempted=2,
                succeeded=0,
                needs_reauth=False,
                account_failures=[
                    AccountFailure(
                        account_id=5,
                        kind=FailureKind.NO_DOWNLOAD,
                        message="empty",
                    )
                ],
            )
            == "failed"
        )


def test_download_login_records_no_download_as_failed_run(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "BANK_AGENT_FERNET_KEY", "6cbW1FlbhKbMfjnF2hUNMSmti2-5Y9vOwGRmdQvpzBE="
    )
    store = AgentStore(tmp_path / "agent.db")
    login = store.add_login(institution_slug="bofa", nickname="personal")
    store.set_storage_state(login.id, json.dumps({"cookies": [], "origins": []}))
    store.set_login_status(login.id, "active")
    store.add_account(
        login_id=login.id,
        storage_uri="gdrive://folder",
        activity_url="https://secure.bankofamerica.com/activity?adx=abc123",
        flow="deposit",
        detected_account_name="BofA Personal",
    )

    class FakeAdapter:
        async def download_account(self, page, *, activity_url, flow, download_dir):
            raise NoDownloadError("BoFA download did not produce a file.")

    fake_pw = AsyncMock()
    fake_browser = AsyncMock()
    fake_context = AsyncMock()
    fake_page = AsyncMock()
    fake_pw.chromium.launch = AsyncMock(return_value=fake_browser)
    fake_browser.new_context = AsyncMock(return_value=fake_context)
    fake_context.new_page = AsyncMock(return_value=fake_page)
    fake_browser.close = AsyncMock()

    with (
        patch("scripts.bank_sync.worker.async_playwright") as mock_playwright,
        patch("scripts.bank_sync.worker.get_adapter", return_value=FakeAdapter()),
    ):
        mock_playwright.return_value.__aenter__.return_value = fake_pw
        outcome = asyncio.run(download_login(store, login.id, kind="manual_download"))

    assert outcome.attempted == 1
    assert outcome.succeeded == 0
    assert outcome.run_status == "failed"
    assert outcome.failure_kind == FailureKind.NO_DOWNLOAD
    assert parse_failure_kind(outcome.failure_reason) == FailureKind.NO_DOWNLOAD

    updated_login = store.get_login(login.id)
    assert updated_login is not None
    assert parse_failure_kind(updated_login.last_failure_reason) == FailureKind.NO_DOWNLOAD

    runs = store.list_runs(login.id, limit=1)
    assert runs[0].status == "failed"
    assert parse_failure_kind(runs[0].error) == FailureKind.NO_DOWNLOAD


def test_download_login_stops_on_needs_reauth(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "BANK_AGENT_FERNET_KEY", "6cbW1FlbhKbMfjnF2hUNMSmti2-5Y9vOwGRmdQvpzBE="
    )
    store = AgentStore(tmp_path / "agent.db")
    login = store.add_login(institution_slug="bofa", nickname="personal")
    store.set_storage_state(login.id, json.dumps({"cookies": [], "origins": []}))
    store.set_login_status(login.id, "active")
    store.add_account(
        login_id=login.id,
        storage_uri="gdrive://folder",
        activity_url="https://secure.bankofamerica.com/activity?adx=abc123",
        flow="deposit",
        detected_account_name="BofA Personal",
    )

    class FakeAdapter:
        async def download_account(self, page, *, activity_url, flow, download_dir):
            raise NeedsReauthError("BoFA redirected to sign-in")

    fake_pw = AsyncMock()
    fake_browser = AsyncMock()
    fake_context = AsyncMock()
    fake_page = AsyncMock()
    fake_pw.chromium.launch = AsyncMock(return_value=fake_browser)
    fake_browser.new_context = AsyncMock(return_value=fake_context)
    fake_context.new_page = AsyncMock(return_value=fake_page)
    fake_browser.close = AsyncMock()

    with (
        patch("scripts.bank_sync.worker.async_playwright") as mock_playwright,
        patch("scripts.bank_sync.worker.get_adapter", return_value=FakeAdapter()),
    ):
        mock_playwright.return_value.__aenter__.return_value = fake_pw
        outcome = asyncio.run(download_login(store, login.id, kind="manual_download"))

    assert outcome.needs_reauth is True
    assert outcome.failure_kind == FailureKind.NEEDS_REAUTH
    updated_login = store.get_login(login.id)
    assert updated_login is not None
    assert updated_login.status == "needs_reauth"
