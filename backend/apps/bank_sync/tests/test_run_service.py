"""Tests for the SyncRun queue and outcome handling."""

from __future__ import annotations

from django.utils import timezone

from apps.bank_sync.models import BankLogin, SyncedAccount, SyncRun
from apps.bank_sync.services import login_service, run_service


def _login(user, institution, **kwargs):
    return BankLogin.objects.create(
        user=user,
        institution=institution,
        nickname=kwargs.pop("nickname", "Personal"),
        status=kwargs.pop("status", "active"),
        cadence=kwargs.pop("cadence", "daily"),
        next_run_at=kwargs.pop("next_run_at", None),
    )


def test_queue_interactive_login_supersedes_pending(alice, bofa_institution):
    login = _login(alice, bofa_institution, status="pending_login")
    first = run_service.queue_interactive_login(login)
    second = run_service.queue_interactive_login(login)
    first.refresh_from_db()
    assert first.status == "failed"
    assert first.failure_kind == "login_cancelled"
    assert second.status == "queued"


def test_queue_manual_download_bumps_next_run_at(alice, bofa_institution):
    login = _login(alice, bofa_institution)
    run = run_service.queue_manual_download(login)
    login.refresh_from_db()
    assert run.task_kind == "manual_download"
    assert run.triggered_by == "manual"
    assert login.next_run_at is not None


def test_lease_due_tasks_picks_queued_first(alice, bofa_institution):
    login = _login(alice, bofa_institution)
    login_service.bind_account(
        bank_login=login,
        financial_account=alice_factory(login, "Checking", "checking"),
        flow="deposit",
        activity_url="https://bofa.test/activity?adx=A1",
    )
    run = run_service.queue_manual_download(login)
    leased = run_service.lease_due_tasks()
    assert any(r.id == run.id for r in leased)
    run.refresh_from_db()
    assert run.status == "running"
    assert run.leased_at is not None


def test_lease_creates_scheduled_download_for_past_due_login(alice, bofa_institution):
    login = _login(
        alice,
        bofa_institution,
        next_run_at=timezone.now() - timezone.timedelta(minutes=1),
    )
    leased = run_service.lease_due_tasks()
    kinds = {r.task_kind for r in leased if r.bank_login_id == login.id}
    assert "scheduled_download" in kinds


def test_record_outcome_success_resets_failures(alice, bofa_institution):
    login = _login(alice, bofa_institution)
    login.consecutive_failures = 2
    login.last_failure_reason = "earlier"
    login.save()
    run = SyncRun.objects.create(bank_login=login, task_kind="scheduled_download", status="running")
    run_service.record_outcome(
        run,
        succeeded=True,
        accounts_attempted=1,
        accounts_succeeded=1,
        statements_imported=1,
    )
    login.refresh_from_db()
    run.refresh_from_db()
    assert run.status == "completed"
    assert login.consecutive_failures == 0
    assert login.last_failure_reason == ""
    assert login.last_success_at is not None


def test_record_outcome_needs_reauth_flips_login(alice, bofa_institution):
    login = _login(alice, bofa_institution)
    run = SyncRun.objects.create(bank_login=login, task_kind="scheduled_download", status="running")
    run_service.record_outcome(
        run,
        succeeded=False,
        failure_kind="needs_reauth",
        failure_reason="session expired",
    )
    login.refresh_from_db()
    assert login.status == "needs_reauth"
    assert login.next_run_at is None


def test_record_outcome_three_failures_marks_error(alice, bofa_institution):
    login = _login(alice, bofa_institution)
    login.consecutive_failures = 2
    login.save()
    run = SyncRun.objects.create(bank_login=login, task_kind="scheduled_download", status="running")
    run_service.record_outcome(
        run,
        succeeded=False,
        failure_kind="dom_broken",
        failure_reason="selector missing",
    )
    login.refresh_from_db()
    assert login.status == "error"
    assert login.consecutive_failures == 3


# Helper used inline above so test fixtures stay focused on accounts that
# already exist; bind_account requires a FinancialAccount with the same
# user, which the global fixtures don't always provide for the scenario.
def alice_factory(login: BankLogin, name: str, account_type: str):
    from decimal import Decimal

    from apps.financial_account.models import FinancialAccount

    return FinancialAccount.objects.create(
        user=login.user,
        name=name,
        institution=login.institution,
        account_type=account_type,
        balance=Decimal("0.00"),
    )


def test_bind_sets_sync_mode_auto(alice, bofa_institution, alice_checking):
    login = _login(alice, bofa_institution)
    login_service.bind_account(
        bank_login=login,
        financial_account=alice_checking,
        flow="deposit",
        activity_url="https://bofa.test/activity?adx=A1",
        external_account_token="A1",
    )
    alice_checking.refresh_from_db()
    assert alice_checking.sync_mode == "auto"
    assert SyncedAccount.objects.filter(financial_account=alice_checking).exists()


def test_unbind_resets_sync_mode(alice, bofa_institution, alice_checking):
    login = _login(alice, bofa_institution)
    synced = login_service.bind_account(
        bank_login=login,
        financial_account=alice_checking,
        flow="deposit",
    )
    login_service.unbind_account(synced)
    alice_checking.refresh_from_db()
    assert alice_checking.sync_mode == "manual"
    assert not SyncedAccount.objects.filter(financial_account=alice_checking).exists()
