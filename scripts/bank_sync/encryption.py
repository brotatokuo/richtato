"""Local Fernet encryption for the host bank-agent.

The agent persists cookies + bank activity URLs inside its own SQLite
database (``local_data/bank-agent/agent.db``). They are encrypted at
rest with a Fernet key loaded from the ``BANK_AGENT_FERNET_KEY``
environment variable so the file is useless to anyone without that key.

This key is **separate** from the backend's ``BANK_SYNC_FERNET_KEY`` —
the agent and the app share no secrets, only a filesystem path.
"""

from __future__ import annotations

import os
from functools import lru_cache

from cryptography.fernet import Fernet


class MissingAgentKey(RuntimeError):
    """Raised when ``BANK_AGENT_FERNET_KEY`` is unset."""


@lru_cache(maxsize=1)
def _cipher() -> Fernet:
    key = os.environ.get("BANK_AGENT_FERNET_KEY", "").strip()
    if not key:
        raise MissingAgentKey(
            "BANK_AGENT_FERNET_KEY is not set. Generate one with:\n"
            "  python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'\n"
            "and add it to your shell profile (do not commit it)."
        )
    try:
        return Fernet(key.encode())
    except Exception as exc:
        raise MissingAgentKey(f"BANK_AGENT_FERNET_KEY is not a valid Fernet key: {exc}") from exc


def encrypt_text(plaintext: str) -> str:
    """Encrypt a UTF-8 string; returns ASCII ciphertext."""
    if not plaintext:
        return ""
    return _cipher().encrypt(plaintext.encode()).decode()


def decrypt_text(ciphertext: str) -> str:
    """Decrypt ASCII Fernet ciphertext back to a UTF-8 string."""
    if not ciphertext:
        return ""
    return _cipher().decrypt(ciphertext.encode()).decode()


def generate_key() -> str:
    """Return a fresh Fernet key as an ASCII string."""
    return Fernet.generate_key().decode()
