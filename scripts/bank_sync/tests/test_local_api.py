"""Tests for the bank-agent local HTTP API."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

from scripts.bank_sync.agent_store import AgentStore
from scripts.bank_sync.local_api import BankAgentApiServer


def _start_server(store: AgentStore, token: str = ""):
    server = BankAgentApiServer(("127.0.0.1", 0), store, token=token)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}"


def _request(url: str, *, token: str = ""):
    request = urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def test_status_redacts_activity_urls(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "BANK_AGENT_FERNET_KEY", "6cbW1FlbhKbMfjnF2hUNMSmti2-5Y9vOwGRmdQvpzBE="
    )
    store = AgentStore(tmp_path / "agent.db")
    login = store.add_login(institution_slug="bofa", nickname="personal")
    store.add_account(
        login_id=login.id,
        storage_uri="gdrive://folder",
        activity_url="https://bank.example/activity?secret=1",
        flow="deposit",
        detected_account_name="Checking",
        richtato_account_id=123,
    )
    server, base_url = _start_server(store)
    try:
        payload = _request(f"{base_url}/status")
    finally:
        server.shutdown()

    assert payload["login_count"] == 1
    account = payload["logins"][0]["accounts"][0]
    assert account["has_activity_url"] is True
    assert "activity_url" not in account
    assert "secret=1" not in json.dumps(payload)


def test_status_requires_token_when_configured(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "BANK_AGENT_FERNET_KEY", "6cbW1FlbhKbMfjnF2hUNMSmti2-5Y9vOwGRmdQvpzBE="
    )
    store = AgentStore(tmp_path / "agent.db")
    server, base_url = _start_server(store, token="local-token")
    try:
        try:
            _request(f"{base_url}/status")
        except urllib.error.HTTPError as exc:
            assert exc.code == 401
        else:
            raise AssertionError("Expected unauthorized response")

        payload = _request(f"{base_url}/status", token="local-token")
    finally:
        server.shutdown()

    assert payload["ok"] is True
