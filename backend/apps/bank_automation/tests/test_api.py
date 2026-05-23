"""Integration tests for the bank automation API."""

from __future__ import annotations

import json

import pytest
from rest_framework.test import APIClient

from apps.bank_automation.models import BankConnection, BankSession
from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.richtato_user.models import User


@pytest.fixture
def user(db):
    user = User.objects.create_user(username="captureuser", password="password123")
    return user


@pytest.fixture
def institution(db):
    """Reuse the data-migration BofA row if present, else create one.

    The seed migration ships ``Bank of America`` with slug
    ``bank_of_america``, while the bank-automation runner expects ``bofa``.
    Realign the slug so test data agrees with the runner adapter naming.
    """

    inst = FinancialInstitution.objects.filter(slug="bofa").first()
    if inst:
        return inst
    inst = FinancialInstitution.objects.filter(name="Bank of America").first()
    if inst:
        inst.slug = "bofa"
        inst.save(update_fields=["slug"])
        return inst
    return FinancialInstitution.objects.create(name="Bank of America", slug="bofa")


@pytest.fixture
def authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def financial_account(user, institution):
    return FinancialAccount.objects.create(
        user=user,
        name="BofA Checking",
        institution=institution,
        account_type="checking",
        balance=0,
    )


def test_list_connections_empty(authed_client):
    response = authed_client.get("/api/v1/bank-automation/connections/")
    assert response.status_code == 200
    assert response.data == {"connections": []}


def test_capture_session_creates_connection_and_session(authed_client, user, institution, financial_account):
    payload = {
        "institution_slug": "bofa",
        "login_id": "bofa_personal",
        "nickname": "BofA Personal",
        "storage_state": {"cookies": [{"name": "x", "value": "y", "domain": "bankofamerica.com"}]},
        "accounts": [
            {
                "flow": "deposit",
                "activity_url": "https://secure.bankofamerica.com/deposit-details/activity/?adx=TOK1",
                "external_account_token": "TOK1",
                "detected_account_name": "Adv Plus Banking ...1234",
                "financial_account_id": financial_account.id,
            }
        ],
    }
    response = authed_client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201, response.data
    body = response.data
    assert body["institution_slug"] == "bofa"
    assert body["login_id"] == "bofa_personal"
    assert body["status"] == "active"
    assert body["next_run_at"] is not None  # daily cadence => scheduled
    assert len(body["account_links"]) == 1
    assert body["account_links"][0]["financial_account"] == financial_account.id

    connection = BankConnection.objects.get(user=user, login_id="bofa_personal")
    session = BankSession.objects.get(connection=connection)
    decrypted = session.get_storage_state()
    assert json.loads(decrypted)["cookies"][0]["value"] == "y"


def test_patch_connection_updates_cadence_and_reschedules(authed_client, user, institution, financial_account):
    """PATCH should change the cadence and recompute next_run_at."""

    # Seed a connection.
    seed = {
        "institution_slug": "bofa",
        "login_id": "bofa_seed",
        "storage_state": {},
        "accounts": [
            {
                "flow": "deposit",
                "activity_url": "https://example.com",
                "financial_account_id": financial_account.id,
            }
        ],
    }
    create_resp = authed_client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps(seed),
        content_type="application/json",
    )
    pk = create_resp.data["id"]
    initial_next_run = create_resp.data["next_run_at"]

    response = authed_client.patch(
        f"/api/v1/bank-automation/connections/{pk}/",
        data=json.dumps({"cadence": "weekly", "preferred_run_hour_local": 9}),
        content_type="application/json",
    )
    assert response.status_code == 200, response.data
    assert response.data["cadence"] == "weekly"
    assert response.data["preferred_run_hour_local"] == 9
    # Reschedule should produce a different timestamp than the initial daily 6 AM.
    assert response.data["next_run_at"] != initial_next_run


def test_patch_connection_to_manual_clears_next_run_at(authed_client, user, institution, financial_account):
    seed = {
        "institution_slug": "bofa",
        "login_id": "bofa_manual",
        "storage_state": {},
        "accounts": [
            {
                "flow": "deposit",
                "activity_url": "https://example.com",
                "financial_account_id": financial_account.id,
            }
        ],
    }
    create_resp = authed_client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps(seed),
        content_type="application/json",
    )
    pk = create_resp.data["id"]

    response = authed_client.patch(
        f"/api/v1/bank-automation/connections/{pk}/",
        data=json.dumps({"cadence": "manual"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.data["cadence"] == "manual"
    assert response.data["next_run_at"] is None


def test_disable_connection(authed_client, user, institution, financial_account):
    seed = {
        "institution_slug": "bofa",
        "login_id": "bofa_disable",
        "storage_state": {},
        "accounts": [
            {
                "flow": "deposit",
                "activity_url": "https://example.com",
                "financial_account_id": financial_account.id,
            }
        ],
    }
    create_resp = authed_client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps(seed),
        content_type="application/json",
    )
    pk = create_resp.data["id"]

    response = authed_client.post(f"/api/v1/bank-automation/connections/{pk}/disable/")
    assert response.status_code == 200
    assert response.data["status"] == "disabled"
    assert response.data["next_run_at"] is None


def test_delete_connection_removes_session(authed_client, user, institution, financial_account):
    seed = {
        "institution_slug": "bofa",
        "login_id": "bofa_delete",
        "storage_state": {},
        "accounts": [
            {
                "flow": "deposit",
                "activity_url": "https://example.com",
                "financial_account_id": financial_account.id,
            }
        ],
    }
    create_resp = authed_client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps(seed),
        content_type="application/json",
    )
    pk = create_resp.data["id"]

    response = authed_client.delete(f"/api/v1/bank-automation/connections/{pk}/")
    assert response.status_code == 204
    assert not BankConnection.objects.filter(pk=pk).exists()
    assert not BankSession.objects.filter(connection_id=pk).exists()


def test_supported_institutions(authed_client, institution):
    response = authed_client.get("/api/v1/bank-automation/supported-institutions/")
    assert response.status_code == 200
    slugs = [i["slug"] for i in response.data["institutions"]]
    assert "bofa" in slugs


def test_bindable_accounts_filters_and_flags(authed_client, user, institution, financial_account):
    """The bindable-accounts endpoint surfaces matching accounts first and
    flags ones that are already bound to a connection."""

    chase, _ = FinancialInstitution.objects.get_or_create(slug="chase", defaults={"name": "Chase"})
    other_account = FinancialAccount.objects.create(
        user=user,
        name="Chase Sapphire",
        institution=chase,
        account_type="credit_card",
        is_liability=True,
        balance=0,
    )

    seed = {
        "institution_slug": "bofa",
        "login_id": "bofa_bind",
        "storage_state": {},
        "accounts": [
            {
                "flow": "deposit",
                "activity_url": "https://example.com",
                "financial_account_id": financial_account.id,
            }
        ],
    }
    authed_client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps(seed),
        content_type="application/json",
    )

    response = authed_client.get("/api/v1/bank-automation/bindable-accounts/?institution_slug=bofa")
    assert response.status_code == 200, response.data
    accounts = response.data["accounts"]
    by_id = {a["id"]: a for a in accounts}

    bofa_entry = by_id[financial_account.id]
    assert bofa_entry["matches_institution"] is True
    assert bofa_entry["already_bound"] is True
    assert bofa_entry["flow"] == "deposit"

    chase_entry = by_id[other_account.id]
    assert chase_entry["matches_institution"] is False
    assert chase_entry["already_bound"] is False
    assert chase_entry["flow"] == "credit_card"

    # Matching institution should sort ahead of non-matching even though it
    # is "already_bound" — the popup needs to show every option.
    assert accounts[0]["matches_institution"] is True


def test_bindable_accounts_unknown_institution_returns_all(authed_client, financial_account):
    response = authed_client.get("/api/v1/bank-automation/bindable-accounts/?institution_slug=does-not-exist")
    assert response.status_code == 200
    accounts = response.data["accounts"]
    assert any(a["id"] == financial_account.id for a in accounts)
    # No slug match, so no entry should be flagged matches_institution.
    assert all(a["matches_institution"] is False for a in accounts)


def test_capture_session_unauthenticated_rejected():
    client = APIClient()
    response = client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps({"institution_slug": "bofa", "login_id": "x", "storage_state": {}, "accounts": []}),
        content_type="application/json",
    )
    assert response.status_code in (401, 403)


def test_runner_due_connections_returns_decrypted_payload(authed_client, user, institution, financial_account):
    """The runner endpoint exposes decrypted storage_state for due connections."""

    seed = {
        "institution_slug": "bofa",
        "login_id": "bofa_runner",
        "storage_state": {"cookies": [{"name": "k", "value": "v"}]},
        "accounts": [
            {
                "flow": "deposit",
                "activity_url": "https://secure.bankofamerica.com/?adx=ABC",
                "external_account_token": "ABC",
                "financial_account_id": financial_account.id,
            }
        ],
    }
    create_resp = authed_client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps(seed),
        content_type="application/json",
    )
    assert create_resp.status_code == 201

    response = authed_client.get("/api/v1/bank-automation/runner/due-connections/?all=1")
    assert response.status_code == 200, response.data
    body = response.data
    assert len(body["connections"]) == 1
    payload = body["connections"][0]
    assert payload["institution_slug"] == "bofa"
    assert payload["login_id"] == "bofa_runner"
    decoded = json.loads(payload["storage_state"])
    assert decoded["cookies"][0]["value"] == "v"
    assert payload["accounts"][0]["activity_url"] == seed["accounts"][0]["activity_url"]
    assert payload["accounts"][0]["financial_account_id"] == financial_account.id
    # A leased run row should have been created.
    assert payload["run_id"] is not None


def test_runner_run_outcome_records_success_and_recomputes_next_run(
    authed_client, user, institution, financial_account
):
    seed = {
        "institution_slug": "bofa",
        "login_id": "bofa_outcome_ok",
        "storage_state": {},
        "accounts": [
            {
                "flow": "deposit",
                "activity_url": "https://example.com",
                "financial_account_id": financial_account.id,
            }
        ],
    }
    authed_client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps(seed),
        content_type="application/json",
    )

    due = authed_client.get("/api/v1/bank-automation/runner/due-connections/?all=1")
    run_id = due.data["connections"][0]["run_id"]

    response = authed_client.post(
        f"/api/v1/bank-automation/runner/runs/{run_id}/outcome/",
        data=json.dumps(
            {
                "succeeded": True,
                "accounts_attempted": 1,
                "accounts_succeeded": 1,
                "statements_imported": 1,
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200, response.data
    assert response.data["run"]["status"] == "completed"
    assert response.data["connection_status"] == "active"
    assert response.data["next_run_at"] is not None


def test_runner_run_outcome_session_expired_marks_reauth(authed_client, user, institution, financial_account):
    seed = {
        "institution_slug": "bofa",
        "login_id": "bofa_outcome_expired",
        "storage_state": {},
        "accounts": [
            {
                "flow": "deposit",
                "activity_url": "https://example.com",
                "financial_account_id": financial_account.id,
            }
        ],
    }
    authed_client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps(seed),
        content_type="application/json",
    )
    due = authed_client.get("/api/v1/bank-automation/runner/due-connections/?all=1")
    run_id = due.data["connections"][0]["run_id"]

    response = authed_client.post(
        f"/api/v1/bank-automation/runner/runs/{run_id}/outcome/",
        data=json.dumps(
            {
                "succeeded": False,
                "failure_kind": "session_expired",
                "failure_reason": "redirected to login",
                "accounts_attempted": 1,
                "accounts_succeeded": 0,
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200, response.data
    assert response.data["run"]["status"] == "failed"
    assert response.data["run"]["failure_kind"] == "session_expired"
    assert response.data["connection_status"] == "reauth_required"
    assert response.data["next_run_at"] is None


def test_runner_run_outcome_other_user_404(authed_client, institution):
    other = User.objects.create_user(username="otheruser", password="x")
    other_client = APIClient()
    other_client.force_authenticate(user=other)
    response = other_client.post(
        "/api/v1/bank-automation/runner/runs/99999/outcome/",
        data=json.dumps({"succeeded": True}),
        content_type="application/json",
    )
    assert response.status_code == 404


def test_other_users_connection_not_visible(authed_client, user, institution, financial_account):
    # Create a connection for a different user.
    other = User.objects.create_user(username="other", password="x")
    other_account = FinancialAccount.objects.create(
        user=other,
        name="Other BofA",
        institution=institution,
        account_type="checking",
        balance=0,
    )
    other_client = APIClient()
    other_client.force_authenticate(user=other)
    other_client.post(
        "/api/v1/bank-automation/sessions/",
        data=json.dumps(
            {
                "institution_slug": "bofa",
                "login_id": "other_login",
                "storage_state": {},
                "accounts": [
                    {
                        "flow": "deposit",
                        "activity_url": "https://example.com",
                        "financial_account_id": other_account.id,
                    }
                ],
            }
        ),
        content_type="application/json",
    )

    response = authed_client.get("/api/v1/bank-automation/connections/")
    assert response.status_code == 200
    assert response.data["connections"] == []
