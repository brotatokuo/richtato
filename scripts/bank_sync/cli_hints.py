"""User-facing CLI command hints for bank-agent output."""

from __future__ import annotations

import os


def signin_command_hint(login_id: int | None = None) -> str:
    """Return the sign-in command appropriate for the active CLI wrapper."""
    if os.environ.get("RICHTATO_CLI"):
        if login_id is not None:
            return f"`richtato bank signin {login_id}`"
        return "`richtato bank signin`"
    if login_id is not None:
        return f"`bank-agent login signin {login_id}`"
    return "`bank-agent login signin <id>`"
