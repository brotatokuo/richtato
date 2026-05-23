"""Tests for the ``import_accounts_json`` management command."""

from __future__ import annotations

import json

import pytest
from django.core.management import CommandError, call_command

from apps.bank_automation.models import BankAccountLink, BankConnection, BankSession
from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.richtato_user.models import User


@pytest.fixture
def institution(db):
    inst = FinancialInstitution.objects.filter(slug="bofa").first()
    if inst:
        return inst
    inst = FinancialInstitution.objects.filter(name="Bank of America").first()
    if inst:
        if not inst.slug:
            inst.slug = "bofa"
            inst.save(update_fields=["slug"])
        return inst
    return FinancialInstitution.objects.create(name="Bank of America", slug="bofa")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="migrator", password="x")


@pytest.fixture
def financial_account(user, institution):
    return FinancialAccount.objects.create(
        user=user,
        name="BofA Checking A",
        institution=institution,
        account_type="checking",
        balance=0,
    )


def _write_accounts_files(tmp_path, *, with_placeholder: bool = True):
    storage_dir = tmp_path / "storage_states"
    storage_dir.mkdir()
    state_path = storage_dir / "bofa_a.json"
    state_path.write_text(json.dumps({"cookies": [{"name": "x", "value": "y"}]}))

    accounts_data = {
        "logins": {
            "bofa_a": {"storage_state": "storage_states/bofa_a.json"},
        },
        "accounts": [
            {
                "slug": "bofa_a_checking",
                "login": "bofa_a",
                "institution": "bofa",
                "flow": "deposit",
                "activity_url": "https://secure.bankofamerica.com/?adx=AAA",
            },
        ],
    }
    if with_placeholder:
        accounts_data["accounts"].append(
            {
                "slug": "bofa_a_savings",
                "login": "bofa_a",
                "institution": "bofa",
                "flow": "deposit",
                "activity_url": "REPLACE_WITH_ACTIVITY_URL_INCLUDING_adx_TOKEN",
            }
        )

    accounts_file = tmp_path / "accounts.json"
    accounts_file.write_text(json.dumps(accounts_data))
    return accounts_file, storage_dir


@pytest.mark.django_db
def test_import_creates_connection_session_and_link(tmp_path, user, institution, financial_account):
    accounts_file, storage_dir = _write_accounts_files(tmp_path)

    call_command(
        "import_accounts_json",
        username="migrator",
        accounts_file=str(accounts_file),
        storage_states_dir=str(storage_dir),
        account_id_map=json.dumps({"bofa_a_checking": financial_account.id}),
    )

    connection = BankConnection.objects.get(user=user, login_id="bofa_a")
    assert connection.institution.slug == "bofa"
    assert connection.cadence == "daily"
    assert connection.status == "active"

    session = BankSession.objects.get(connection=connection)
    decoded = json.loads(session.get_storage_state())
    assert decoded["cookies"][0]["value"] == "y"

    links = list(BankAccountLink.objects.filter(connection=connection))
    assert len(links) == 1  # placeholder skipped
    assert links[0].financial_account_id == financial_account.id
    assert links[0].activity_url.startswith("https://secure.bankofamerica.com/")


@pytest.mark.django_db
def test_import_dry_run_does_not_persist(tmp_path, user, institution):
    accounts_file, storage_dir = _write_accounts_files(tmp_path, with_placeholder=False)

    call_command(
        "import_accounts_json",
        username="migrator",
        accounts_file=str(accounts_file),
        storage_states_dir=str(storage_dir),
        dry_run=True,
    )
    assert not BankConnection.objects.filter(login_id="bofa_a").exists()


@pytest.mark.django_db
def test_import_unknown_user_raises(tmp_path, db):
    accounts_file, storage_dir = _write_accounts_files(tmp_path, with_placeholder=False)

    with pytest.raises(CommandError):
        call_command(
            "import_accounts_json",
            username="nope",
            accounts_file=str(accounts_file),
            storage_states_dir=str(storage_dir),
        )


@pytest.mark.django_db
def test_import_is_idempotent(tmp_path, user, institution, financial_account):
    accounts_file, storage_dir = _write_accounts_files(tmp_path, with_placeholder=False)

    for _ in range(2):
        call_command(
            "import_accounts_json",
            username="migrator",
            accounts_file=str(accounts_file),
            storage_states_dir=str(storage_dir),
            account_id_map=json.dumps({"bofa_a_checking": financial_account.id}),
        )

    assert BankConnection.objects.filter(user=user, login_id="bofa_a").count() == 1
