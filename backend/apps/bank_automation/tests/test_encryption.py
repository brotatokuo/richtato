"""Tests for the Fernet encryption helpers."""

from __future__ import annotations

import json

from apps.bank_automation.encryption import decrypt_text, encrypt_text


def test_round_trip_simple_string():
    plaintext = "hello world"
    token = encrypt_text(plaintext)
    assert token != plaintext
    assert decrypt_text(token) == plaintext


def test_round_trip_url_with_query_params():
    plaintext = (
        "https://secure.bankofamerica.com/deposit-details/activity/"
        "?adx=ae0a1955f2135b7f83d8865246dcd75c&source=overview"
    )
    token = encrypt_text(plaintext)
    assert "adx" not in token
    assert decrypt_text(token) == plaintext


def test_round_trip_storage_state_json():
    storage_state = {
        "cookies": [{"name": "session", "value": "abc", "domain": ".example.com"}],
        "origins": [{"origin": "https://example.com", "localStorage": []}],
    }
    plaintext = json.dumps(storage_state)
    token = encrypt_text(plaintext)
    decrypted = decrypt_text(token)
    assert json.loads(decrypted) == storage_state


def test_empty_string_passthrough():
    assert encrypt_text("") == ""
    assert decrypt_text("") == ""


def test_user_keyed_round_trip():
    plaintext = "secret cookie value"
    token = encrypt_text(plaintext, user_id=42)
    assert token.startswith("u1:42:")
    assert decrypt_text(token) == plaintext
    assert decrypt_text(token, user_id=42) == plaintext


def test_user_keys_are_per_user():
    """Tokens encrypted for one user must not be decryptable as another."""

    import pytest

    plaintext = "user-specific"
    token = encrypt_text(plaintext, user_id=1)

    with pytest.raises(Exception):
        decrypt_text(token, user_id=2)


def test_user_keyed_token_diverges_from_account_wide():
    plaintext = "compare me"
    user_token = encrypt_text(plaintext, user_id=1)
    account_token = encrypt_text(plaintext)
    assert user_token != account_token
    assert decrypt_text(user_token) == plaintext
    assert decrypt_text(account_token) == plaintext


def test_legacy_token_still_decrypts():
    """Tokens written without a user key remain readable after the upgrade."""

    plaintext = "legacy"
    legacy = encrypt_text(plaintext)
    assert not legacy.startswith("u1:")
    assert decrypt_text(legacy) == plaintext
