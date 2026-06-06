"""Per-user envelope encryption for stored secrets.

Currently this protects the Google Drive OAuth refresh token persisted on
``GoogleDriveConnection``. The plaintext is never logged or returned in API
responses.

Two key derivations are supported so multi-tenant deployments can keep one
user's leaked ciphertext from compromising another:

* **Account-wide key**: a single Fernet key from ``BANK_SYNC_FERNET_KEY``.
  Used when no ``user_id`` is supplied and as a backstop for legacy rows
  written before per-user envelopes were introduced.
* **Per-user envelope key**: a 32-byte HMAC-SHA256 of
  ``f"bank_sync:{user_id}"`` keyed with the master key. Tokens are prefixed
  ``u1:{user_id}:...`` so :func:`decrypt_text` can route to the right key
  without an extra DB column.

The master key lives in ``BANK_SYNC_FERNET_KEY`` (env). In dev, a missing
value falls back to a deterministic key derived from ``SECRET_KEY`` so local
development needs no extra setup. Production must always set it explicitly.

The ``BANK_SYNC_FERNET_KEY`` setting name and the ``bank_sync:{user_id}`` key
derivation string are retained intentionally so ciphertext written before the
bank-sync removal still decrypts.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

from django.conf import settings

_USER_KEY_PREFIX = "u1:"


def _derive_dev_key() -> bytes:
    """Derive a deterministic 32-byte Fernet key from Django ``SECRET_KEY``."""

    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _master_key_bytes() -> bytes:
    """Return the raw 32-byte master key (decoded from base64-urlsafe)."""

    raw_key = getattr(settings, "BANK_SYNC_FERNET_KEY", None)
    if raw_key:
        encoded = raw_key.encode("utf-8") if isinstance(raw_key, str) else raw_key
    else:
        encoded = _derive_dev_key()
    return base64.urlsafe_b64decode(encoded)


def _derive_user_key(user_id: int) -> bytes:
    """Derive a 32-byte key bound to ``user_id`` from the master key."""

    msg = f"bank_sync:{int(user_id)}".encode()
    return hmac.new(_master_key_bytes(), msg, hashlib.sha256).digest()


def get_fernet(*, user_id: int | None = None):
    """Return a Fernet instance for the given ``user_id`` (account-wide if None).

    Importing ``cryptography`` lazily keeps the app importable when the
    library is not installed (e.g. running migrations on a fresh checkout).
    """

    from cryptography.fernet import Fernet

    if user_id is None:
        raw_key = getattr(settings, "BANK_SYNC_FERNET_KEY", None)
        if raw_key:
            key = raw_key.encode("utf-8") if isinstance(raw_key, str) else raw_key
        else:
            key = _derive_dev_key()
    else:
        key = base64.urlsafe_b64encode(_derive_user_key(user_id))
    return Fernet(key)


def encrypt_text(plaintext: str, *, user_id: int | None = None) -> str:
    """Encrypt ``plaintext`` and return a urlsafe base64 string.

    Empty input is passed through unchanged so blank fields don't accumulate
    ciphertext that decrypts back to an empty string. When ``user_id`` is
    supplied the result is prefixed ``u1:{user_id}:`` so the decrypt path can
    pick the right key without a separate "key id" column on every row.
    """

    if not plaintext:
        return ""
    token = get_fernet(user_id=user_id).encrypt(plaintext.encode("utf-8"))
    encoded = token.decode("utf-8")
    if user_id is not None:
        return f"{_USER_KEY_PREFIX}{user_id}:{encoded}"
    return encoded


def decrypt_text(token: str, *, user_id: int | None = None) -> str:
    """Decrypt a token produced by :func:`encrypt_text`.

    Tokens prefixed with ``u1:`` are decrypted with the per-user key encoded
    in the prefix; others fall back to the account-wide key. ``user_id`` is
    accepted as a sanity check against the prefix when both are present.
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
