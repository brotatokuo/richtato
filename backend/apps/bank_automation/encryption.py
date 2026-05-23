"""Symmetric encryption helpers for sensitive bank automation fields.

Storage state cookies and bank activity URLs (with per-account `adx` tokens)
are sensitive credentials at rest. We encrypt them with Fernet so a database
dump alone is not enough to drive a session.

Two key derivations are supported:

* **Account-wide key** (Phase 1): a single Fernet key from
  ``BANK_AUTOMATION_FERNET_KEY``. Used when no ``user_id`` is supplied, and
  for legacy ciphertext that was encrypted before the per-user upgrade.
* **Per-user envelope key** (Phase 2): a 32-byte HMAC-SHA256 of
  ``f"bank_automation:{user_id}"`` keyed with the master key. This means a
  database leak that exposes one user's ciphertext does not let an attacker
  decrypt another user's payload without also leaking the per-user key.

The Fernet key lives in the ``BANK_AUTOMATION_FERNET_KEY`` env var. In dev,
if the key is missing we fall back to a deterministic key derived from
``SECRET_KEY`` so local testing works without extra setup. Production must
always set ``BANK_AUTOMATION_FERNET_KEY``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

from django.conf import settings

# Marker prefix on tokens encrypted with a user-scoped key. Lets us round-trip
# both legacy account-wide tokens and new per-user tokens transparently.
_USER_KEY_PREFIX = "u1:"


def _derive_dev_key() -> bytes:
    """Derive a deterministic 32-byte Fernet key from Django ``SECRET_KEY``.

    Used as a development convenience only. The Fernet primitive accepts
    base64-urlsafe-encoded 32-byte keys, so we hash the secret to a fixed
    length first.
    """

    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _master_key_bytes() -> bytes:
    """Return the raw 32-byte master key (decoded from base64-urlsafe)."""

    raw_key = getattr(settings, "BANK_AUTOMATION_FERNET_KEY", None)
    if raw_key:
        encoded = raw_key.encode("utf-8") if isinstance(raw_key, str) else raw_key
    else:
        encoded = _derive_dev_key()
    return base64.urlsafe_b64decode(encoded)


def _derive_user_key(user_id: int) -> bytes:
    """Derive a 32-byte key bound to ``user_id`` from the master key."""

    msg = f"bank_automation:{int(user_id)}".encode()
    return hmac.new(_master_key_bytes(), msg, hashlib.sha256).digest()


def get_fernet(*, user_id: int | None = None):
    """Return a Fernet instance for the given ``user_id`` (account-wide if None).

    Importing ``cryptography`` lazily keeps the app importable when the
    library is not installed (e.g. running migrations on a fresh checkout).
    """

    from cryptography.fernet import Fernet

    if user_id is None:
        raw_key = getattr(settings, "BANK_AUTOMATION_FERNET_KEY", None)
        if raw_key:
            key = raw_key.encode("utf-8") if isinstance(raw_key, str) else raw_key
        else:
            key = _derive_dev_key()
    else:
        key = base64.urlsafe_b64encode(_derive_user_key(user_id))
    return Fernet(key)


def encrypt_text(plaintext: str, *, user_id: int | None = None) -> str:
    """Encrypt ``plaintext`` and return a urlsafe base64 string.

    Empty / falsy input is passed through unchanged so that empty fields
    don't accumulate ciphertext that decrypts back to an empty string.

    When ``user_id`` is supplied, the resulting token is prefixed with
    ``"u1:"`` so :func:`decrypt_text` can pick the right key without storing
    a separate "kid" column on every row.
    """

    if not plaintext:
        return ""
    token = get_fernet(user_id=user_id).encrypt(plaintext.encode("utf-8"))
    encoded = token.decode("utf-8")
    if user_id is not None:
        return f"{_USER_KEY_PREFIX}{user_id}:{encoded}"
    return encoded


def decrypt_text(token: str, *, user_id: int | None = None) -> str:
    """Decrypt a token produced by :func:`encrypt_text`. Empty input returns ``""``.

    Tokens prefixed with ``"u1:"`` are decrypted with the per-user key
    embedded in the prefix; other tokens fall back to the account-wide key.
    The explicit ``user_id`` argument is accepted for symmetry but is only
    used as a sanity check against the prefix when both are present.
    """

    if not token:
        return ""

    if token.startswith(_USER_KEY_PREFIX):
        try:
            _, embedded_user_id, payload = token.split(":", 2)
            embedded_user_id_int = int(embedded_user_id)
        except (ValueError, TypeError) as exc:
            raise ValueError("Malformed user-keyed token") from exc
        if user_id is not None and int(user_id) != embedded_user_id_int:
            raise ValueError("user_id mismatch on user-keyed token")
        fernet = get_fernet(user_id=embedded_user_id_int)
        return fernet.decrypt(payload.encode("utf-8")).decode("utf-8")

    return get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
