"""End-to-end tests for the bank-sync REST API.

Covers the headed-login lifecycle: create login -> queue interactive login
-> agent captures session -> binding step -> account becomes auto-synced.
Also exercises the agent-only runner endpoints (token auth) and the
manual sync-now path.
"""

from __future__ import annotations

import json

import pytest
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.bank_sync.models import BankLogin, SyncedAccount, SyncRun
from apps.bank_sync.services import session_service


@pytest.fixture
def alice_client(alice):
    client = APIClient()
    client.force_authenticate(user=alice)
    return client


@pytest.fixture
def runner_client(runner_user):
    token, _ = Token.objects.get_or_create(user=runner_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def test_create_login_starts_pending(alice_client, bofa_institution):
    url = reverse("bank-sync-login-list")
    response = alice_client.post(
        url,
        {"institution": bofa_institution.id, "nickname": "Personal", "cadence": "daily"},
        format="json",
    )
    assert response.status_code == 201, response.data
    data = response.data
    assert data["status"] == "pending_login"
    assert data["nickname"] == "Personal"


def test_create_login_rejects_unsupported_institution(alice_client, db):
    from apps.financial_account.models import FinancialInstitution

    inst, _ = FinancialInstitution.objects.get_or_create(
        slug="random_neobank",
        defaults={"name": "Random Neobank"},
    )
    url = reverse("bank-sync-login-list")
    response = alice_client.post(
        url,
        {"institution": inst.id, "cadence": "daily"},
        format="json",
    )
    assert response.status_code == 400


def test_begin_login_queues_interactive_task(alice_client, bofa_institution):
    create = alice_client.post(
        reverse("bank-sync-login-list"),
        {"institution": bofa_institution.id, "cadence": "daily"},
        format="json",
    )
    login_id = create.data["id"]
    begin = alice_client.post(reverse("bank-sync-login-begin-login", args=[login_id]))
    assert begin.status_code == 202
    run = SyncRun.objects.get(bank_login_id=login_id)
    assert run.task_kind == "interactive_login"
    assert run.status == "queued"


def test_sync_now_rejects_pending_login(alice_client, bofa_institution):
    create = alice_client.post(
        reverse("bank-sync-login-list"),
        {"institution": bofa_institution.id, "cadence": "daily"},
        format="json",
    )
    login_id = create.data["id"]
    response = alice_client.post(reverse("bank-sync-login-sync-now", args=[login_id]))
    assert response.status_code == 400
    assert response.data["status"] == "pending_login"


def test_runner_due_tasks_returns_queued_interactive_login(alice_client, runner_client, bofa_institution):
    create = alice_client.post(
        reverse("bank-sync-login-list"),
        {"institution": bofa_institution.id, "cadence": "daily"},
        format="json",
    )
    login_id = create.data["id"]
    alice_client.post(reverse("bank-sync-login-begin-login", args=[login_id]))

    response = runner_client.get(reverse("bank-sync-runner-due-tasks"))
    assert response.status_code == 200, response.data
    tasks = response.data["tasks"]
    assert any(t["task_kind"] == "interactive_login" and t["bank_login_id"] == login_id for t in tasks)


def test_runner_captured_session_flips_login_active(alice_client, runner_client, alice, bofa_institution):
    # Bootstrap a login + run leased to the agent.
    create = alice_client.post(
        reverse("bank-sync-login-list"),
        {"institution": bofa_institution.id, "cadence": "daily"},
        format="json",
    )
    login_id = create.data["id"]
    alice_client.post(reverse("bank-sync-login-begin-login", args=[login_id]))
    runner_client.get(reverse("bank-sync-runner-due-tasks"))
    run_id = SyncRun.objects.get(bank_login_id=login_id).id

    storage_state = {"cookies": [{"name": "session", "value": "abc"}], "origins": []}
    response = runner_client.post(
        reverse("bank-sync-runner-captured-session", args=[run_id]),
        {
            "storage_state": storage_state,
            "discovered_accounts": [
                {
                    "detected_account_name": "BofA Checking ····1234",
                    "external_account_token": "ADX1",
                    "activity_url": "https://bofa.test/activity?adx=ADX1",
                    "flow": "deposit",
                },
            ],
        },
        format="json",
    )
    assert response.status_code == 200, response.data

    login = BankLogin.objects.get(pk=login_id)
    assert login.status == "active"
    assert login.cookies_captured_at is not None
    assert json.loads(session_service.get_storage_state(login))["cookies"][0]["value"] == "abc"


def test_runner_outcome_needs_reauth_flips_login(alice_client, runner_client, alice, bofa_institution, alice_checking):
    # Create + activate a login via the same headed-capture path.
    create = alice_client.post(
        reverse("bank-sync-login-list"),
        {"institution": bofa_institution.id, "cadence": "daily"},
        format="json",
    )
    login_id = create.data["id"]
    alice_client.post(reverse("bank-sync-login-begin-login", args=[login_id]))
    runner_client.get(reverse("bank-sync-runner-due-tasks"))
    run_id = SyncRun.objects.get(bank_login_id=login_id).id
    runner_client.post(
        reverse("bank-sync-runner-captured-session", args=[run_id]),
        {"storage_state": {}, "discovered_accounts": []},
        format="json",
    )
    runner_client.post(
        reverse("bank-sync-runner-run-outcome", args=[run_id]),
        {"succeeded": True, "accounts_attempted": 0, "accounts_succeeded": 0},
        format="json",
    )
    # Bind, then simulate a needs_reauth failure on the next scheduled run.
    alice_client.post(
        reverse("bank-sync-synced-account-bulk-bind"),
        {
            "accounts": [
                {
                    "bank_login": login_id,
                    "financial_account": alice_checking.id,
                    "flow": "deposit",
                    "activity_url": "https://bofa.test/activity?adx=ADX1",
                    "external_account_token": "ADX1",
                    "detected_account_name": "Checking",
                }
            ]
        },
        format="json",
    )
    sync_run = SyncRun.objects.create(
        bank_login_id=login_id,
        task_kind="scheduled_download",
        status="running",
    )
    response = runner_client.post(
        reverse("bank-sync-runner-run-outcome", args=[sync_run.id]),
        {"succeeded": False, "failure_kind": "needs_reauth", "failure_reason": "expired"},
        format="json",
    )
    assert response.status_code == 200, response.data
    login = BankLogin.objects.get(pk=login_id)
    assert login.status == "needs_reauth"


def test_bulk_bind_sets_sync_mode_auto(alice_client, alice, bofa_institution, alice_checking):
    create = alice_client.post(
        reverse("bank-sync-login-list"),
        {"institution": bofa_institution.id, "cadence": "daily"},
        format="json",
    )
    login_id = create.data["id"]
    response = alice_client.post(
        reverse("bank-sync-synced-account-bulk-bind"),
        {
            "accounts": [
                {
                    "bank_login": login_id,
                    "financial_account": alice_checking.id,
                    "flow": "deposit",
                    "external_account_token": "ADX9",
                    "detected_account_name": "Checking",
                    "activity_url": "https://bofa.test/activity?adx=ADX9",
                }
            ]
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    alice_checking.refresh_from_db()
    assert alice_checking.sync_mode == "auto"
    assert SyncedAccount.objects.filter(financial_account=alice_checking).count() == 1


def test_bindable_accounts_filters_by_institution(alice_client, alice, bofa_institution, chase_institution):
    from decimal import Decimal

    from apps.financial_account.models import FinancialAccount

    FinancialAccount.objects.create(
        user=alice,
        name="Match",
        institution=bofa_institution,
        account_type="checking",
        balance=Decimal("0"),
    )
    FinancialAccount.objects.create(
        user=alice,
        name="Other",
        institution=chase_institution,
        account_type="checking",
        balance=Decimal("0"),
    )
    response = alice_client.get(
        reverse("bank-sync-bindable-accounts"),
        {"institution_slug": "bofa"},
    )
    assert response.status_code == 200
    by_name = {a["name"]: a for a in response.data["accounts"]}
    assert by_name["Match"]["matches_institution"] is True
    assert by_name["Other"]["matches_institution"] is False


def test_runner_due_tasks_filters_by_task_kind(alice_client, runner_client, bofa_institution):
    create = alice_client.post(
        reverse("bank-sync-login-list"),
        {"institution": bofa_institution.id, "cadence": "daily"},
        format="json",
    )
    login_id = create.data["id"]
    alice_client.post(reverse("bank-sync-login-begin-login", args=[login_id]))

    interactive = runner_client.get(
        reverse("bank-sync-runner-due-tasks"),
        {"task_kinds": "interactive_login"},
    ).data["tasks"]
    downloads = runner_client.get(
        reverse("bank-sync-runner-due-tasks"),
        {"task_kinds": "scheduled_download,manual_download"},
    ).data["tasks"]

    assert interactive and all(t["task_kind"] == "interactive_login" for t in interactive)
    assert not downloads


def test_end_user_cannot_hit_runner_endpoints(alice_client):
    response = alice_client.get(reverse("bank-sync-runner-due-tasks"))
    assert response.status_code in (401, 403)
