"""Tests for bank-agent apply env block handling."""

import os
from argparse import Namespace
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from scripts.bank_sync.agent import _apply_config_payload, _apply_env_block, cmd_sync
from scripts.bank_sync.agent_store import AgentStore


@pytest.fixture(autouse=True)
def clear_agent_env(monkeypatch):
    for key in ("RICHTATO_API_TOKEN", "BANK_AGENT_FERNET_KEY"):
        monkeypatch.delenv(key, raising=False)


class TestApplyEnvBlock:
    def test_sets_credentials_from_env_block(self):
        _apply_env_block(
            {
                "RICHTATO_API_TOKEN": "test-token",
                "BANK_AGENT_FERNET_KEY": "test-fernet-key",
            }
        )

        assert os.environ["RICHTATO_API_TOKEN"] == "test-token"
        assert os.environ["BANK_AGENT_FERNET_KEY"] == "test-fernet-key"

    def test_ignores_missing_or_invalid_env_block(self):
        _apply_env_block(None)
        _apply_env_block("not-a-dict")

        assert "RICHTATO_API_TOKEN" not in os.environ
        assert "BANK_AGENT_FERNET_KEY" not in os.environ

    def test_cmd_apply_loads_env_before_applying_logins(self, tmp_path):
        config_path = tmp_path / "setup.yml"
        config_path.write_text(
            "\n".join(
                [
                    "env:",
                    '  RICHTATO_API_TOKEN: "yaml-token"',
                    '  BANK_AGENT_FERNET_KEY: "yaml-fernet"',
                    "logins: []",
                ]
            )
        )

        with patch("scripts.bank_sync.agent._apply_config_payload", return_value=0) as mock_apply:
            from argparse import Namespace

            from scripts.bank_sync.agent import cmd_apply

            result = cmd_apply(Namespace(config=str(config_path), db=None))

        assert result == 0
        assert os.environ["RICHTATO_API_TOKEN"] == "yaml-token"
        assert os.environ["BANK_AGENT_FERNET_KEY"] == "yaml-fernet"
        mock_apply.assert_called_once()


class TestApplyActivityUrl:
    def test_apply_writes_activity_url_to_account(self, tmp_path, monkeypatch):
        monkeypatch.setenv("BANK_AGENT_FERNET_KEY", "6cbW1FlbhKbMfjnF2hUNMSmti2-5Y9vOwGRmdQvpzBE=")
        store = AgentStore(tmp_path / "agent.db")

        result = _apply_config_payload(
            {
                "logins": [
                    {
                        "institution": "bofa",
                        "nickname": "personal",
                        "cadence": "daily",
                        "hour": 6,
                        "accounts": [
                            {
                                "name": "BofA Personal",
                                "flow": "deposit",
                                "storage_uri": "gdrive://folder",
                                "richtato_account_id": 302,
                                "activity_url": "https://secure.bankofamerica.com/activity?adx=abc123",
                            }
                        ],
                    }
                ],
            },
            store,
        )

        assert result == 0
        account = store.list_accounts()[0]
        assert account.activity_url == "https://secure.bankofamerica.com/activity?adx=abc123"

    def test_apply_clears_activity_url_when_yaml_is_blank(self, tmp_path, monkeypatch):
        monkeypatch.setenv("BANK_AGENT_FERNET_KEY", "6cbW1FlbhKbMfjnF2hUNMSmti2-5Y9vOwGRmdQvpzBE=")
        store = AgentStore(tmp_path / "agent.db")
        login = store.add_login(institution_slug="bofa", nickname="personal")
        store.add_account(
            login_id=login.id,
            storage_uri="gdrive://folder",
            activity_url="https://secure.bankofamerica.com/activity?adx=abc123",
            flow="deposit",
            detected_account_name="BofA Personal",
            richtato_account_id=302,
        )

        result = _apply_config_payload(
            {
                "logins": [
                    {
                        "institution": "bofa",
                        "nickname": "personal",
                        "cadence": "daily",
                        "hour": 6,
                        "accounts": [
                            {
                                "name": "BofA Personal",
                                "flow": "deposit",
                                "storage_uri": "gdrive://folder",
                                "richtato_account_id": 302,
                                "activity_url": "",
                            }
                        ],
                    }
                ],
            },
            store,
        )

        assert result == 0
        account = store.list_accounts()[0]
        assert account.activity_url == ""


class TestApplySourceOfTruth:
    def test_apply_removes_stale_login_not_in_yaml(self, tmp_path, monkeypatch):
        monkeypatch.setenv("BANK_AGENT_FERNET_KEY", "6cbW1FlbhKbMfjnF2hUNMSmti2-5Y9vOwGRmdQvpzBE=")
        store = AgentStore(tmp_path / "agent.db")
        store.add_login(institution_slug="chase", nickname="personal")

        result = _apply_config_payload(
            {
                "logins": [
                    {
                        "institution": "bofa",
                        "nickname": "personal",
                        "cadence": "daily",
                        "hour": 6,
                        "accounts": [
                            {
                                "name": "BofA Checking",
                                "flow": "deposit",
                                "storage_uri": "gdrive://folder",
                                "richtato_account_id": 1,
                            }
                        ],
                    }
                ],
            },
            store,
        )

        assert result == 0
        logins = store.list_logins()
        assert len(logins) == 1
        assert logins[0].institution_slug == "bofa"

    def test_apply_removes_stale_account_not_in_yaml(self, tmp_path, monkeypatch):
        monkeypatch.setenv("BANK_AGENT_FERNET_KEY", "6cbW1FlbhKbMfjnF2hUNMSmti2-5Y9vOwGRmdQvpzBE=")
        store = AgentStore(tmp_path / "agent.db")
        login = store.add_login(institution_slug="bofa", nickname="personal")
        store.add_account(
            login_id=login.id,
            storage_uri="gdrive://old-folder",
            flow="deposit",
            detected_account_name="Old Account",
            richtato_account_id=999,
        )

        result = _apply_config_payload(
            {
                "logins": [
                    {
                        "institution": "bofa",
                        "nickname": "personal",
                        "cadence": "daily",
                        "hour": 6,
                        "accounts": [
                            {
                                "name": "BofA Checking",
                                "flow": "deposit",
                                "storage_uri": "gdrive://new-folder",
                                "richtato_account_id": 1,
                            }
                        ],
                    }
                ],
            },
            store,
        )

        assert result == 0
        accounts = store.list_accounts()
        assert len(accounts) == 1
        assert accounts[0].storage_uri == "gdrive://new-folder"

    def test_apply_preserves_cookies_for_kept_login(self, tmp_path, monkeypatch):
        monkeypatch.setenv("BANK_AGENT_FERNET_KEY", "6cbW1FlbhKbMfjnF2hUNMSmti2-5Y9vOwGRmdQvpzBE=")
        store = AgentStore(tmp_path / "agent.db")
        login = store.add_login(institution_slug="bofa", nickname="personal")
        store.set_storage_state(login.id, '{"cookies": [{"name": "session", "value": "abc"}]}')
        store.add_account(
            login_id=login.id,
            storage_uri="gdrive://folder",
            flow="deposit",
            detected_account_name="BofA Checking",
            richtato_account_id=1,
        )

        _apply_config_payload(
            {
                "logins": [
                    {
                        "institution": "bofa",
                        "nickname": "personal",
                        "cadence": "daily",
                        "hour": 6,
                        "accounts": [
                            {
                                "name": "BofA Checking",
                                "flow": "deposit",
                                "storage_uri": "gdrive://folder",
                                "richtato_account_id": 1,
                            }
                        ],
                    }
                ],
            },
            store,
        )

        kept = store.list_logins()[0]
        assert kept.cookies_captured_at is not None
        assert "session" in kept.storage_state


class TestSyncHeaded:
    def test_cmd_sync_passes_headed_to_worker(self):
        calls = []

        class FakeWorker:
            async def download_login(self, store, login_id, *, kind, headed):
                calls.append(
                    {
                        "store": store,
                        "login_id": login_id,
                        "kind": kind,
                        "headed": headed,
                    }
                )
                return SimpleNamespace(
                    attempted=1,
                    succeeded=1,
                    files_downloaded=1,
                    failure_reason="",
                    needs_reauth=False,
                    failure_kind=None,
                    account_failures=[],
                    run_status="completed",
                )

        fake_store = object()
        with (
            patch("scripts.bank_sync.agent._store", return_value=fake_store),
            patch("scripts.bank_sync.agent._lazy_worker", return_value=FakeWorker()),
        ):
            result = cmd_sync(Namespace(login_id=1, headed=True, db=None))

        assert result == 0
        assert calls == [
            {
                "store": fake_store,
                "login_id": 1,
                "kind": "manual_download",
                "headed": True,
            }
        ]
