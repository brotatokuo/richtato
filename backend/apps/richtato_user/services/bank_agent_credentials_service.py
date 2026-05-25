"""Bank-agent host credential helpers."""

from __future__ import annotations

from cryptography.fernet import Fernet
from rest_framework.authtoken.models import Token

from apps.richtato_user.models import User, UserPreference


def get_or_create_bank_agent_fernet_key(user: User) -> str:
    """Return a stable Fernet key for encrypting the host agent vault."""
    preference, _ = UserPreference.objects.get_or_create(user=user)
    if preference.bank_agent_fernet_key:
        return preference.bank_agent_fernet_key

    key = Fernet.generate_key().decode()
    preference.bank_agent_fernet_key = key
    preference.save(update_fields=["bank_agent_fernet_key"])
    return key


def get_bank_agent_credentials(user: User) -> dict[str, str]:
    """Return the user's API token and bank-agent Fernet key."""
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "fernet_key": get_or_create_bank_agent_fernet_key(user),
    }
