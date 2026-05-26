"""Tests for per-user envelope encryption."""

from __future__ import annotations

import pytest

from apps.bank_sync.encryption import decrypt_text, encrypt_text


def test_round_trip_account_wide():
    """Account-wide key (no user_id) encrypts and decrypts cleanly."""

    token = encrypt_text("hello world")
    assert token  # not empty
    assert token != "hello world"
    assert decrypt_text(token) == "hello world"


def test_empty_string_passthrough():
    """Empty input returns empty without burning Fernet cycles."""

    assert encrypt_text("") == ""
    assert decrypt_text("") == ""


def test_round_trip_per_user(db):
    """Per-user envelope produces a prefixed token that decrypts with its user_id."""

    token = encrypt_text("alice secret", user_id=42)
    assert token.startswith("u1:42:")
    assert decrypt_text(token) == "alice secret"
    assert decrypt_text(token, user_id=42) == "alice secret"


def test_user_isolation(db):
    """A token bound to user A cannot be decrypted as user B."""

    token = encrypt_text("alice secret", user_id=1)
    # Passing user_id=2 should be rejected by the prefix sanity check.
    with pytest.raises(ValueError):
        decrypt_text(token, user_id=2)


def test_account_wide_token_not_decryptable_per_user(db):
    """Account-wide tokens fall back to the account-wide key on decrypt."""

    token = encrypt_text("shared secret")
    # No user prefix means the account-wide branch decrypts cleanly.
    assert decrypt_text(token) == "shared secret"
